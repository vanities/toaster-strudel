// Tokenizer + note-reference helpers, ported from the vanilla player. Pure
// functions so the code panel can render syntax spans and build shift-click
// references without touching the audio engine.

export interface Token {
  type: 'comment' | 'string' | 'number' | 'method' | 'fn' | 'ident' | 'op';
  start: number;
  end: number;
  text: string;
}

const STRUDEL_FNS = new Set([
  'setcps', 'stack', 'note', 's', 'cat', 'seq', 'sine', 'saw', 'sawtooth', 'square',
  'triangle', 'cos', 'perlin', 'silence', 'hush', 'white', 'bd', 'sd', 'hh', 'cp', 'oh', 'pink',
]);

export function tokenize(code: string): Token[] {
  const tokens: Token[] = [];
  let i = 0;
  while (i < code.length) {
    const rest = code.slice(i);
    let m: RegExpMatchArray | null;
    if ((m = rest.match(/^\/\/[^\n]*/))) {
      tokens.push({ type: 'comment', start: i, end: i + m[0].length, text: m[0] });
      i += m[0].length;
      continue;
    }
    if ((m = rest.match(/^"(?:[^"\\]|\\.)*"/))) {
      tokens.push({ type: 'string', start: i, end: i + m[0].length, text: m[0] });
      i += m[0].length;
      continue;
    }
    if ((m = rest.match(/^\d+\.?\d*/))) {
      tokens.push({ type: 'number', start: i, end: i + m[0].length, text: m[0] });
      i += m[0].length;
      continue;
    }
    if ((m = rest.match(/^[a-zA-Z_$][\w$]*/))) {
      const isMethod = i > 0 && code[i - 1] === '.';
      const type = isMethod ? 'method' : STRUDEL_FNS.has(m[0]) ? 'fn' : 'ident';
      tokens.push({ type, start: i, end: i + m[0].length, text: m[0] });
      i += m[0].length;
      continue;
    }
    tokens.push({ type: 'op', start: i, end: i + 1, text: code[i] });
    i++;
  }
  return tokens;
}

export interface NoteRef {
  track: string | null;
  segment: string;
  line: number;
  col: number;
  start: number;
  end: number;
  text: string;
  lineText: string;
}

// Build a chat-ready reference for the token at a source offset. (No audition
// map enrichment yet — note/instrument come in stage 2 with the highlight tap.)
export function noteRefAt(
  code: string,
  offset: number,
  track: string | null,
  segment: string
): NoteRef | null {
  if (!code) return null;
  let line = 1;
  let lineStart = 0;
  for (let i = 0; i < offset && i < code.length; i++) {
    if (code[i] === '\n') {
      line++;
      lineStart = i + 1;
    }
  }
  let lineEnd = code.indexOf('\n', offset);
  if (lineEnd === -1) lineEnd = code.length;

  const tok = /[A-Za-z0-9#._:-]/;
  let start = offset;
  let end = offset;
  while (start > lineStart && tok.test(code[start - 1])) start--;
  while (end < lineEnd && tok.test(code[end])) end++;
  if (start === end) end = Math.min(offset + 1, code.length);

  return {
    track,
    segment,
    line,
    col: offset - lineStart + 1,
    start,
    end,
    text: code.slice(start, end),
    lineText: code.slice(lineStart, lineEnd).trim(),
  };
}
