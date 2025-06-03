import React from 'react';
import Layout from '@/components/Layout';

export function withLayout<P extends Object>(Component: React.ComponentType<P>): React.FC<P> {
  const Wrapped: React.FC<P> = (props) => (
    <Layout>
      <Component {...props} />
    </Layout>
  );

  Wrapped.displayName = `withLayout(${Component.displayName || Component.name || 'Component'})`;
  return Wrapped;
}
