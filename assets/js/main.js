import { nav } from './partials/nav.js';
import { hero } from './partials/hero.js';
import { showcase } from './partials/showcase.js';
import { modules } from './partials/modules.js';
import { philosophy } from './partials/philosophy.js';
import { themes } from './partials/themes.js';
import { architecture } from './partials/architecture.js';
import { api } from './partials/api.js';
import { install } from './partials/install.js';
import { shortcuts } from './partials/shortcuts.js';
import { github } from './partials/github.js';
import { footer } from './partials/footer.js';
import { initSite } from './site.js';

const app = document.getElementById('app');
const sections = [hero, showcase, modules, philosophy, themes, architecture, api, install, shortcuts, github];

if (app) {
  app.innerHTML = [
    '<a href="#content" class="sr-only">Pular para o conteudo</a>',
    nav,
    '<main id="content">',
    ...sections,
    '</main>',
    footer,
  ].join('\n');

  initSite();
}
