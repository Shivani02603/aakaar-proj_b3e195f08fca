import React from 'react';
import classNames from 'classnames';
import ReactMarkdown from 'react-markdown';

interface MessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ role, content, sources }) => {
  const isUser = role === 'user';

  const handleSourceClick = (source: string) => {
    navigator.clipboard.writeText(source).catch((err) => {
      console.error('Failed to copy source text:', err);
    });
  };

  return (
    <div className={classNames('flex', { 'justify-end': isUser, 'justify-start': !isUser })}>
      <div
        className={classNames(
          'max-w-lg p-4 rounded-lg shadow-md',
          {
            'bg-blue-500 text-white': isUser,
            'bg-gray-200 text-gray-800': !isUser,
          }
        )}
      >
        <ReactMarkdown className="prose">{content}</ReactMarkdown>
        {!isUser && sources && sources.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {sources.map((source, index) => (
              <button
                key={index}
                onClick={() => handleSourceClick(source)}
                className="text-xs bg-gray-300 text-gray-700 px-2 py-1 rounded-full hover:bg-gray-400"
              >
                {source}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;