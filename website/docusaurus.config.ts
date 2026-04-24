import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Behavior Latticing',
  tagline: 'Behavior Latticing — inferring user motivations from unstructured interactions',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://stanfordhci.github.io',
  baseUrl: '/lattice',

  staticDirectories: ['static'],

  organizationName: 'stanfordhci',
  projectName: 'lattice',

  trailingSlash: false,

  onBrokenLinks: 'throw',
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/stanfordhci/lattice/tree/main/website/',
        },
        blog: {
          routeBasePath: 'gallery',
          blogTitle: 'Gallery',
          blogSidebarTitle: 'All Posts',
          blogSidebarCount: 'ALL',
          postsPerPage: 'ALL',
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Behavior Latticing',
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        {
          to: '/gallery',
          label: 'Gallery',
          position: 'left',
        },
        {
          href: 'https://github.com/stanfordhci/lattice',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            { label: 'Getting Started', to: '/docs/intro' },
            { label: 'API Reference', to: '/docs/api/lattice' },
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/stanfordhci/lattice',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Stanford HCI Group. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['python', 'json', 'bash'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
