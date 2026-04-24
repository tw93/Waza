// @ts-check
import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'static',
  // If deploying to GitHub Pages at tw93.github.io/Waza, uncomment:
  // site: 'https://tw93.github.io',
  // base: '/Waza',
  //
  // If deploying to a custom domain (e.g. waza.tw93.fun), uncomment:
  // site: 'https://waza.tw93.fun',
  build: {
    assets: '_assets',
  },
});
