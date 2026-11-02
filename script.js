const translations = {
  en: {
    "skip": "Skip to content",
    "language": "Site language",
    "nav.home": "Home",
    "nav.experience": "Experience",
    "nav.projects": "Projects",
    "nav.education": "Education",
    "nav.about": "About",
    "nav.contact": "Contact",
    "nav.open": "Open menu",
    "nav.close": "Close menu",
    "hero.eyebrow": "Data Engineering · AI Engineering · Data Governance",
    "hero.title": "Reliable data, clear processes, useful solutions.",
    "hero.intro": "I'm Samuel Okotako. I work with data management and am developing my path toward junior roles in Data Engineering, AI Engineering and Data Governance.",
    "hero.projects": "Explore projects",
    "hero.contact": "Get in touch",
    "hero.focusLabel": "Focus",
    "hero.focusTitle": "From raw data to usable data",
    "hero.focus1": "Data pipelines and transformations",
    "hero.focus2": "Data quality, governance and protection",
    "hero.focus3": "Study and experimentation in AI Engineering",
    "hero.focusNote": "Technologies featured in the projects: SQL, dbt, DuckDB, Databricks and Arduino.",
    "featured.eyebrow": "Featured",
    "featured.title": "Projects to explore",
    "experience.eyebrow": "Professional path",
    "experience.title": "Experience",
    "experience.intro": "Hands-on experience described without exposing internal material or processes.",
    "experience.type": "Internship",
    "experience.date": "June – October 2026",
    "experience.area": "Areas of work: Data Governance, Data Masking and pseudonymization.",
    "experience.doneTitle": "Actual work",
    "experience.done": "The internship covered these areas. Specific activities and publishable outcomes will be added after verification, without confidential company material.",
    "experience.studiedTitle": "Skills under study",
    "experience.studied": "Work on data pipelines, dbt, DuckDB, Databricks and AI Engineering is presented in projects or education, without attributing it to the internship.",
    "projects.eyebrow": "Work and experiments",
    "projects.title": "Projects",
    "projects.intro": "Each card separates known facts from details still to be documented. No metrics are reported without evidence.",
    "project.private": "Details to verify",
    "project.pending": "Documentation in progress",
    "project.school": "Final school project",
    "label.problem": "Problem",
    "label.goal": "Goal",
    "label.tech": "Technology",
    "label.solution": "Solution",
    "label.result": "Outcome",
    "project.governance.title": "Data Governance & Masking",
    "project.governance.problem": "Protect sensitive data while keeping it manageable in governance processes.",
    "project.governance.goal": "Explore masking and pseudonymization in the internship context.",
    "project.governance.tech": "Tools and platforms cannot be published without verification.",
    "project.governance.solution": "Implementation details to verify before publication.",
    "project.governance.result": "No publishable quantitative outcome is documented in the repository.",
    "project.governance.note": "No company code or documents are published.",
    "project.dbt.title": "dbt + DuckDB pipeline",
    "project.dbt.problem": "Turn raw data into reproducible analytical models.",
    "project.dbt.goal": "Organize a local data transformation pipeline.",
    "project.dbt.solution": "Pipeline structure and steps to be documented with the project code.",
    "project.dbt.result": "Tests and verifiable outcomes to be added.",
    "project.repoPending": "Public repository link to be added after verification.",
    "project.nosql.title": "NoSQL Big Data with Databricks",
    "project.nosql.problem": "Manage and analyze non-relational data on a Big Data platform.",
    "project.nosql.goal": "Document a NoSQL workflow in Databricks.",
    "project.nosql.tech": "Databricks · NoSQL; detailed stack to verify.",
    "project.nosql.solution": "Architecture, dataset and implementation to be documented.",
    "project.nosql.result": "Verifiable outcomes to be added.",
    "project.radar.title": "Arduino electronic radar",
    "project.radar.problem": "Detect nearby objects with an educational prototype.",
    "project.radar.goal": "Build the final project for the Electronics and Automation diploma.",
    "project.radar.tech": "Arduino; specific components to confirm.",
    "project.radar.solution": "Prototype for detecting nearby objects. The project included a historical link to the evolution of military technology between World War I and World War II.",
    "project.radar.result": "Presented as a final school project; measurements and technical documentation to verify.",
    "project.radar.education": "See education ↗",
    "future.badge": "Coming later",
    "future.title": "AI Engineering",
    "future.text": "Space reserved for a complete project with a problem statement, architecture, code and verifiable outcomes.",
    "education.eyebrow": "Learning path",
    "education.title": "Education",
    "education.itsDate": "28 October 2026",
    "education.itsDegree": "Higher Technical Diploma in Data Management",
    "education.finalGrade": "Final grade",
    "education.moduleAverage": "Module average",
    "education.modulesSummary": "28 modules and official grades",
    "education.modulesPending": "The official list of 28 modules and their grades is not in the repository. It will appear here after verification; modules without a numeric grade will be marked “Idoneo”.",
    "education.ongoing": "In progress",
    "education.unict": "University of Catania",
    "education.unictDegree": "Bachelor's degree in Computer Science (L-31), in progress.",
    "education.diploma": "Diploma",
    "education.archimedeDegree": "Diploma in Electronics and Automation.",
    "education.radarLink": "Final project: Arduino electronic radar ↗",
    "about.eyebrow": "My path",
    "about.title": "About",
    "about.p1": "My path brings together electronics, data management and computer science. After diplomas in Electronics and Automation and at ITS in Data Management, I am continuing my Computer Science studies at the University of Catania.",
    "about.p2": "I'm interested in systems that make data reliable and usable: transformations, quality, governance and AI applications. I approach problems by understanding the context, testing assumptions and documenting decisions.",
    "about.p3": "I'm looking for junior opportunities in Data Engineering, AI Engineering and Data Governance, where I can keep learning through real problems.",
    "contact.eyebrow": "Let's connect",
    "contact.title": "Contact",
    "contact.intro": "For career opportunities or to discuss a project, write to me by email or on LinkedIn.",
    "contact.soon": "Coming soon",
    "contact.previewTitle": "Contact form",
    "contact.previewText": "The interface is prepared. Sending will be available after a secure message service is enabled.",
    "contact.name": "Name",
    "contact.email": "Email",
    "contact.message": "Message",
    "contact.emailAction": "Email me",
    "footer.top": "Back to top ↑"
  }
};

const navToggle = document.getElementById('navToggle');
const navMenu = document.getElementById('navMenu');
const langSelect = document.getElementById('langSelect');
const year = document.getElementById('year');
const italianText = new Map([...document.querySelectorAll('[data-i18n]')].map((element) => [element, element.textContent]));
document.documentElement.classList.add('js');
if (year) year.textContent = new Date().getFullYear();

function storedLanguage() {
  try { return localStorage.getItem('lang'); } catch { return null; }
}
function saveLanguage(lang) {
  try { localStorage.setItem('lang', lang); } catch { /* Storage may be unavailable. */ }
}
function setMenu(open) {
  if (!navToggle || !navMenu) return;
  navToggle.setAttribute('aria-expanded', String(open));
  navMenu.classList.toggle('nav--open', open);
  const label = open ? (document.documentElement.lang === 'en' ? 'Close menu' : 'Chiudi menu') : (document.documentElement.lang === 'en' ? 'Open menu' : 'Apri menu');
  navToggle.setAttribute('aria-label', label);
  const hiddenLabel = navToggle.querySelector('.visually-hidden');
  if (hiddenLabel) hiddenLabel.textContent = label;
}
function setLanguage(lang) {
  const next = lang === 'en' ? 'en' : 'it';
  document.querySelectorAll('[data-i18n]').forEach((element) => {
    const translation = next === 'en' ? translations.en[element.dataset.i18n] : italianText.get(element);
    if (translation !== undefined) element.textContent = translation;
  });
  document.documentElement.lang = next;
  const description = document.querySelector('meta[name="description"]');
  if (description) description.content = next === 'en' ? 'Samuel Okotako’s portfolio: Data Engineering, AI Engineering and Data Governance. Experience, projects and education.' : 'Portfolio di Samuel Okotako: Data Engineering, AI Engineering e Data Governance. Esperienza, progetti e formazione.';
  if (navMenu) navMenu.setAttribute('aria-label', next === 'en' ? 'Main navigation' : 'Navigazione principale');
  if (langSelect) {
    langSelect.value = next;
    langSelect.setAttribute('aria-label', next === 'en' ? 'Site language' : 'Lingua del sito');
  }
  saveLanguage(next);
  setMenu(false);
}

setLanguage(storedLanguage() === 'en' ? 'en' : 'it');
if (langSelect) langSelect.addEventListener('change', (event) => setLanguage(event.target.value));
if (navToggle && navMenu) {
  navToggle.addEventListener('click', () => setMenu(navToggle.getAttribute('aria-expanded') !== 'true'));
  navMenu.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => setMenu(false)));
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && navToggle.getAttribute('aria-expanded') === 'true') {
      setMenu(false);
      navToggle.focus();
    }
  });
  document.addEventListener('click', (event) => {
    if (!navMenu.contains(event.target) && !navToggle.contains(event.target)) setMenu(false);
  });
}
