// ---- NAV MOBILE + YEAR ----
const navToggle = document.getElementById("navToggle");
const navMenu = document.getElementById("navMenu");
const yearSpan = document.getElementById("year");
const langSelect = document.getElementById("langSelect");

if (yearSpan) {
  yearSpan.textContent = new Date().getFullYear();
}

if (navToggle && navMenu) {
  navToggle.addEventListener("click", () => {
    navToggle.classList.toggle("nav-toggle--open");
    navMenu.classList.toggle("nav--open");
  });

  navMenu.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      navToggle.classList.remove("nav-toggle--open");
      navMenu.classList.remove("nav--open");
    });
  });
}

// ---- TRADUZIONI IT / EN ----
const translations = {
  it: {
    "nav.home": "Home",
    "nav.skills": "Skill",
    "nav.projects": "Progetti",
    "nav.about": "Chi sono",
    "nav.contact": "Contatti",

    "hero.eyebrow": "Data Management · Machine Learning · AWS",
    "hero.title": "Trasformo i dati in <span>decisioni misurabili</span>.",
    "hero.subtitle":
      "Mi occupo di pipeline ETL, analisi, modelli di machine learning e integrazione con servizi cloud. L’obiettivo è semplice: usare i dati per prendere decisioni concrete, non intuitive.",
    "hero.btnProjects": "Guarda i progetti",
    "hero.btnContact": "Parliamone",
    "hero.meta1": "📍 Catania",
    "hero.meta2": "🎯 Data · ML · Cloud",
    "hero.cardTitle": "Data Management & Machine Learning",
    "hero.cardText":
      "In questo portfolio trovi progetti reali: pulizia dati, modelli di ML, pipeline ETL e integrazione con servizi cloud come AWS.",
    "hero.tag1": "Python · Pandas · SQL",
    "hero.tag2": "ETL · KPI · Dashboard",
    "hero.tag3": "AWS (S3, Lambda, ecc.)",

    "skills.title": "Skill principali",
    "skills.subtitle":
      "Competenze orientate al ciclo di vita completo del dato: dall’ingest, alla pulizia, fino ai modelli e al reporting.",
    "skills.card1.title": "Data & Feature Engineering",
    "skills.card1.text":
      "Pulizia dati, gestione valori mancanti, encoding, scaling, analisi esplorativa e preparazione dei dati per i modelli.",
    "skills.card1.pill1": "Python",
    "skills.card1.pill2": "Pandas / NumPy",
    "skills.card1.pill3": "EDA · Feature Engineering",

    "skills.card2.title": "Machine Learning",
    "skills.card2.text":
      "Modelli di classificazione e regressione con scikit-learn, valutati con metriche solide e cross-validation.",
    "skills.card2.pill1": "Scikit-learn",
    "skills.card2.pill2": "Classification / Regression",
    "skills.card2.pill3": "Accuracy · F1 · AUC",

    "skills.card3.title": "Cloud & DevOps base",
    "skills.card3.text":
      "Utilizzo di servizi AWS per storage, funzioni serverless e distribuzione di soluzioni basate sui dati.",
    "skills.card3.pill1": "AWS S3",
    "skills.card3.pill2": "AWS Lambda",
    "skills.card3.pill3": "Cloud concetti base",

    "projects.title": "Progetti",
    "projects.subtitle":
      "Alcuni lavori che rappresentano il mio modo di lavorare con i dati: processi chiari, documentati e ripetibili.",
    "projects.card1.title": "Pipeline ETL & Cleaning – Adult Dataset",
    "projects.card1.text":
      "Progetto completo sul dataset Adult (UCI): pulizia, encoding, scaling, analisi esplorativa e preparazione per modelli di classificazione sul reddito.",
    "projects.card1.pill1": "ETL",
    "projects.card1.pill2": "EDA",
    "projects.card1.pill3": "Adult Dataset",
    "projects.card1.link": "Vedi repository →",

    "projects.card2.title": "Modelli di regressione – Temperature oceani",
    "projects.card2.text":
      "Modelli di regressione lineare e avanzati per stimare variazioni di temperatura: feature engineering, selezione feature e analisi dei residui.",
    "projects.card2.pill1": "Regressione",
    "projects.card2.pill2": "R² · MSE",
    "projects.card2.pill3": "Analisi residui",
    "projects.card2.link": "Vedi repository →",

    "projects.card3.title": "RAG su CSV – Prodotti",
    "projects.card3.text":
      "Pipeline RAG che interroga un CSV di prodotti e risponde in linguaggio naturale e in formato JSON strutturato.",
    "projects.card3.pill1": "RAG",
    "projects.card3.pill2": "Embedding + Vector Store",
    "projects.card3.pill3": "JSON Output",
    "projects.card3.link": "Vedi repository →",

    "about.title": "Chi sono",
    "about.p1":
      "Sono Samuel Okotako, specializzato in data management, machine learning e soluzioni data-driven. Lavoro su pipeline ETL, analisi dati, modelli predittivi e integrazione con servizi cloud.",
    "about.p2":
      "Il mio focus è progettare processi chiari, tracciabili e scalabili che trasformano i dati grezzi in insight affidabili e utilizzabili.",
    "about.box1.label": "Formazione",
    "about.box1.text":
      "Informatica & Data Management, con attenzione a ML, cloud e AI generativa.",
    "about.box2.label": "Stile",
    "about.box2.text":
      "Pipeline modulari, documentate, con notebook chiari e repository ordinati.",
    "about.box3.label": "Obiettivo",
    "about.box3.text":
      "Crescere come Data Engineer / ML Engineer e lavorare su progetti in produzione su cloud.",

    "contact.title": "Contatti",
    "contact.subtitle":
      "Per collaborazioni in ambito data management, ML, RAG o progetti cloud.",
    "contact.note":
      "Nei messaggi preferisco chiarezza: contesto, obiettivo, tempi e, se possibile, budget.",
    "contact.form.nameLabel": "Nome*",
    "contact.form.namePlaceholder": "Il tuo nome",
    "contact.form.emailLabel": "Email*",
    "contact.form.emailPlaceholder": "nome@azienda.com",
    "contact.form.subjectLabel": "Oggetto*",
    "contact.form.subjectPlaceholder": "Proposta di collaborazione",
    "contact.form.messageLabel": "Messaggio*",
    "contact.form.messagePlaceholder": "Scrivimi qualche dettaglio sul progetto...",
    "contact.form.button": "Invia",

    "footer.tagline": "Data Management · ML · Cloud"
  },

  en: {
    "nav.home": "Home",
    "nav.skills": "Skills",
    "nav.projects": "Projects",
    "nav.about": "About",
    "nav.contact": "Contact",

    "hero.eyebrow": "Data Management · Machine Learning · AWS",
    "hero.title": "I turn data into <span>measurable decisions</span>.",
    "hero.subtitle":
      "I work on ETL pipelines, analytics, machine learning models and cloud integration. The goal is simple: use data to drive concrete, not intuitive, decisions.",
    "hero.btnProjects": "View projects",
    "hero.btnContact": "Let's talk",
    "hero.meta1": "📍 Catania, Italy",
    "hero.meta2": "🎯 Data · ML · Cloud",
    "hero.cardTitle": "Data Management & Machine Learning",
    "hero.cardText":
      "This portfolio shows real projects: data cleaning, ML models, ETL pipelines and cloud-based solutions on AWS.",
    "hero.tag1": "Python · Pandas · SQL",
    "hero.tag2": "ETL · KPIs · Dashboards",
    "hero.tag3": "AWS (S3, Lambda, etc.)",

    "skills.title": "Core skills",
    "skills.subtitle":
      "Skills focused on the full data lifecycle: from ingest and cleaning to modeling and reporting.",
    "skills.card1.title": "Data & Feature Engineering",
    "skills.card1.text":
      "Data cleaning, missing values handling, encoding, scaling, exploratory analysis and model-ready datasets.",
    "skills.card1.pill1": "Python",
    "skills.card1.pill2": "Pandas / NumPy",
    "skills.card1.pill3": "EDA · Feature Engineering",

    "skills.card2.title": "Machine Learning",
    "skills.card2.text":
      "Classification and regression models with scikit-learn, evaluated with solid metrics and cross-validation.",
    "skills.card2.pill1": "Scikit-learn",
    "skills.card2.pill2": "Classification / Regression",
    "skills.card2.pill3": "Accuracy · F1 · AUC",

    "skills.card3.title": "Cloud & basic DevOps",
    "skills.card3.text":
      "Using AWS services for storage, serverless functions and deployment of data-driven solutions.",
    "skills.card3.pill1": "AWS S3",
    "skills.card3.pill2": "AWS Lambda",
    "skills.card3.pill3": "Cloud basics",

    "projects.title": "Projects",
    "projects.subtitle":
      "A few projects that represent how I work with data: clear, documented and repeatable processes.",
    "projects.card1.title": "ETL & Cleaning Pipeline – Adult Dataset",
    "projects.card1.text":
      "End-to-end project on the Adult (UCI) dataset: cleaning, encoding, scaling, EDA and preparation for income classification models.",
    "projects.card1.pill1": "ETL",
    "projects.card1.pill2": "EDA",
    "projects.card1.pill3": "Adult Dataset",
    "projects.card1.link": "View repository →",

    "projects.card2.title": "Regression models – Ocean temperatures",
    "projects.card2.text":
      "Linear and advanced regression models to estimate temperature variations: feature engineering, feature selection and residuals analysis.",
    "projects.card2.pill1": "Regression",
    "projects.card2.pill2": "R² · MSE",
    "projects.card2.pill3": "Residual analysis",
    "projects.card2.link": "View repository →",

    "projects.card3.title": "RAG on CSV – Products",
    "projects.card3.text":
      "RAG pipeline querying a CSV of products and answering in natural language and structured JSON.",
    "projects.card3.pill1": "RAG",
    "projects.card3.pill2": "Embeddings + Vector Store",
    "projects.card3.pill3": "JSON Output",
    "projects.card3.link": "View repository →",

    "about.title": "About",
    "about.p1":
      "I'm Samuel Okotako, focused on data management, machine learning and data-driven solutions. I work on ETL pipelines, data analysis, predictive models and cloud integration.",
    "about.p2":
      "My focus is designing clear, traceable and scalable processes that turn raw data into reliable, actionable insights.",
    "about.box1.label": "Education",
    "about.box1.text":
      "Computer Science & Data Management, with a strong focus on ML, cloud and generative AI.",
    "about.box2.label": "Approach",
    "about.box2.text":
      "Modular, well-documented pipelines with clear notebooks and organized repositories.",
    "about.box3.label": "Goal",
    "about.box3.text":
      "Grow as a Data Engineer / ML Engineer and work on production-grade projects on cloud.",

    "contact.title": "Contact",
    "contact.subtitle":
      "For collaborations in data management, ML, RAG or cloud projects.",
    "contact.note":
      "In messages I prefer clarity: context, goal, timeline and, if possible, budget.",
    "contact.form.nameLabel": "Name*",
    "contact.form.namePlaceholder": "Your name",
    "contact.form.emailLabel": "Email*",
    "contact.form.emailPlaceholder": "name@company.com",
    "contact.form.subjectLabel": "Subject*",
    "contact.form.subjectPlaceholder": "Collaboration proposal",
    "contact.form.messageLabel": "Message*",
    "contact.form.messagePlaceholder": "Tell me a bit more about the project...",
    "contact.form.button": "Send",

    "footer.tagline": "Data Management · ML · Cloud"
  }
};

function applyTranslations(lang) {
  const dict = translations[lang];
  if (!dict) return;

  // testo interno (innerHTML)
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.dataset.i18n;
    const t = dict[key];
    if (t !== undefined) {
      el.innerHTML = t;
    }
  });

  // placeholder
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.dataset.i18nPlaceholder;
    const t = dict[key];
    if (t !== undefined) {
      el.setAttribute("placeholder", t);
    }
  });

  document.documentElement.lang = lang;
}

function setLanguage(lang) {
  if (!translations[lang]) lang = "it";
  localStorage.setItem("lang", lang);
  if (langSelect) {
    langSelect.value = lang;
  }
  applyTranslations(lang);
}

// Init lingua
const savedLang = localStorage.getItem("lang") || "it";
setLanguage(savedLang);

if (langSelect) {
  langSelect.addEventListener("change", (e) => {
    setLanguage(e.target.value);
  });
}
