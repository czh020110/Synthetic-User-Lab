import { Image } from 'antd';
import { useState } from 'react';
import type { KeyScreenshot } from '../../types/report';
import { screenshotPathToUrl } from '../../api/screenshots';

export default function KeyScreenshots({ screenshots }: { screenshots: KeyScreenshot[] }) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  if (!screenshots || screenshots.length === 0) return null;

  return (
    <>
      <div className="screenshot-grid">
        {screenshots.map((s, i) => {
          const url = screenshotPathToUrl(s.path);
          if (!url) return null;
          return (
            <div
              key={s.path + s.step_index}
              className="screenshot-item"
              onClick={() => setPreviewUrl(url)}
            >
              <img
                src={url}
                alt={s.label || `Screenshot ${i + 1}`}
              />
              {s.label && (
                <div className="screenshot-caption">{s.label}</div>
              )}
            </div>
          );
        })}
      </div>

      <Image
        src={previewUrl || ''}
        style={{ display: 'none' }}
        preview={{
          visible: !!previewUrl,
          src: previewUrl || '',
          onVisibleChange: (visible) => { if (!visible) setPreviewUrl(null); },
        }}
      />
    </>
  );
}
