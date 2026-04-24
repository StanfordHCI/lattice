import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Guides',
      items: [
        'guides/installation',
        'guides/quickstart',
        'guides/data-format',
        'guides/building-layers',
        'guides/visualization',
      ],
    },
    {
      type: 'category',
      label: 'Examples',
      items: [
        'examples/chatgpt',
      ],
    },
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'api/lattice',
        'api/observer',
        'api/llm',
        'api/visualize',
      ],
    },
  ],
};

export default sidebars;
