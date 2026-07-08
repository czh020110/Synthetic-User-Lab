import { Result, Button } from 'antd';
import type { ReactNode } from 'react';
import { Component } from 'react';
import i18n from '../../i18n';

type Props = {
  children: ReactNode;
};

type State = {
  hasError: boolean;
  error?: Error;
};

export default class AppErrorBoundary extends Component<Props, State> {
  state: State = {
    hasError: false,
  };

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: unknown) {
    console.error('AppErrorBoundary caught an error', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="app-error-boundary">
          <Result
            status="500"
            title={i18n.t('errorBoundary.title')}
            subTitle={this.state.error?.message || i18n.t('errorBoundary.subtitle')}
            extra={(
              <Button type="primary" onClick={this.handleReset}>
                {i18n.t('errorBoundary.retry')}
              </Button>
            )}
          />
        </div>
      );
    }

    return this.props.children;
  }
}
