import { Card, Image, Space, Typography } from 'antd';
import type { KeyScreenshot } from '../../types/report';
import { screenshotPathToUrl } from '../../api/screenshots';

const { Title, Text } = Typography;

export default function KeyScreenshots({ screenshots }: { screenshots: KeyScreenshot[] }) {
  if (!screenshots.length) return null;

  return (
    <Card title={<Title level={5} style={{ margin: 0 }}>Key Screenshots</Title>}>
      <Image.PreviewGroup>
        <Space wrap>
          {screenshots.map((s, i) => {
            const url = screenshotPathToUrl(s.path);
            return url ? (
              <div key={i} style={{ textAlign: 'center' }}>
                <Image
                  src={url}
                  width={200}
                  style={{ borderRadius: 4, border: '1px solid #f0f0f0' }}
                  placeholder
                />
                <div><Text type="secondary" style={{ fontSize: 12 }}>{s.label}</Text></div>
              </div>
            ) : null;
          })}
        </Space>
      </Image.PreviewGroup>
    </Card>
  );
}
