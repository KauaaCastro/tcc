import type { ReactNode } from 'react';

type Block =
  | { type: 'p'; lines: string[] }
  | { type: 'ul' | 'ol'; items: string[] }
  | { type: 'h'; level: number; text: string };

// Interpreta negrito, itálico e código inline sem usar HTML bruto
function renderInline(text: string): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*\s][^*]*\*)/g);
  return parts.map((part, index) => {
    if (part.length > 4 && part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    if (part.length > 2 && part.startsWith('`') && part.endsWith('`')) {
      return <code key={index}>{part.slice(1, -1)}</code>;
    }
    if (part.length > 2 && part.startsWith('*') && part.endsWith('*')) {
      return <em key={index}>{part.slice(1, -1)}</em>;
    }
    return part;
  });
}

// Agrupa as linhas em títulos, listas e parágrafos
function parseBlocks(text: string): Block[] {
  const blocks: Block[] = [];
  let current: Block | null = null;

  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line) {
      current = null;
      continue;
    }

    const heading = /^(#{1,4})\s+(.*)$/.exec(line);
    if (heading) {
      blocks.push({ type: 'h', level: heading[1].length, text: heading[2] });
      current = null;
      continue;
    }

    const bullet = /^[-*•]\s+(.*)$/.exec(line);
    const numbered = /^\d+[.)]\s+(.*)$/.exec(line);
    const listType = bullet ? 'ul' : numbered ? 'ol' : null;
    if (listType) {
      const itemText = (bullet ?? numbered)![1];
      if (current && current.type === listType) {
        current.items.push(itemText);
      } else {
        current = { type: listType, items: [itemText] };
        blocks.push(current);
      }
      continue;
    }

    if (current && current.type === 'p') {
      current.lines.push(line);
    } else {
      current = { type: 'p', lines: [line] };
      blocks.push(current);
    }
  }
  return blocks;
}

// Renderiza as respostas da IA com títulos, listas e destaques
export default function MarkdownText({ text }: { text: string }) {
  return (
    <>
      {parseBlocks(text).map((block, index) => {
        if (block.type === 'h') {
          const Tag = block.level <= 2 ? 'h3' : 'h4';
          return <Tag key={index}>{renderInline(block.text)}</Tag>;
        }
        if (block.type === 'p') {
          return (
            <p key={index}>
              {block.lines.map((line, i) => (
                <span key={i}>
                  {i > 0 && <br />}
                  {renderInline(line)}
                </span>
              ))}
            </p>
          );
        }
        const List = block.type;
        return (
          <List key={index}>
            {block.items.map((item, i) => (
              <li key={i}>{renderInline(item)}</li>
            ))}
          </List>
        );
      })}
    </>
  );
}
