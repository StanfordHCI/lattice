import React from 'react';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import type {Props} from '@theme/BlogListPage';
import styles from './styles.module.css';

export default function GalleryPage({metadata, items}: Props) {
  return (
    <Layout title="Gallery" description={metadata.blogDescription}>
      <main className={styles.container}>
        <h1 className={styles.heading}>Gallery</h1>
        Work in progress...
        Check back soon for updates!
        {/* <div className={styles.grid}>
          {items.map(({content: BlogPostContent}) => {
            const {metadata: post} = BlogPostContent;
            return (
              <Link key={post.permalink} to={post.permalink} className={styles.card}>
                <div className={styles.cardTitle}>{post.title}</div>
                <div className={styles.cardDate}>{post.formattedDate}</div>
                {post.description && (
                  <p className={styles.cardDesc}>{post.description}</p>
                )}
              </Link>
            );
          })}
        </div> */}
      </main>
    </Layout>
  );
}
