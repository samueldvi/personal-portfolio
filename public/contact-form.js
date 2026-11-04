/* Formspree contact form. The browser sends content only to the form endpoint. */
(function () {
  'use strict';

  const fieldNames = ['name', 'email', 'reason', 'message'];

  function setupContactForm(form, fetchRequest, FormDataType) {
    if (!form || typeof fetchRequest !== 'function' || typeof FormDataType !== 'function') return null;
    const fields = Object.fromEntries(fieldNames.map((name) => [name, form.elements.namedItem(name)]));
    const errors = Object.fromEntries(fieldNames.map((name) => [name, form.querySelector(`[data-error-for="${name}"]`)]));
    const status = form.querySelector('[data-form-status]');
    const button = form.querySelector('[type="submit"]');
    const honeypot = form.elements.namedItem('_gotcha');
    if (Object.values(fields).some((field) => !field) || Object.values(errors).some((error) => !error) || !status || !button || !honeypot) return null;

    // Keep native HTML5 validation active before the submit event.
    honeypot.value = ''; // Clear values restored by browser autofill or page history.
    let busy = false;
    const buttonLabel = button.textContent;

    function setStatus(key, state) {
      status.textContent = form.dataset[key] || '';
      status.dataset.state = state;
    }

    function clearErrors() {
      for (const name of fieldNames) {
        fields[name].removeAttribute('aria-invalid');
        errors[name].textContent = '';
      }
    }

    function setFieldError(name, key) {
      fields[name].setAttribute('aria-invalid', 'true');
      errors[name].textContent = form.dataset[key] || '';
    }

    function validate() {
      let firstInvalid = null;
      for (const name of fieldNames) {
        const field = fields[name];
        let errorKey = null;
        if (!field.value.trim()) errorKey = 'errorRequired';
        else if (!field.checkValidity()) {
          errorKey = name === 'email' && field.validity.typeMismatch ? 'errorEmail' : 'errorInvalid';
        }
        if (errorKey) {
          setFieldError(name, errorKey);
          firstInvalid ||= field;
        }
      }
      return firstInvalid;
    }

    async function handleSubmit(event) {
      if (busy) {
        event.preventDefault();
        return;
      }
      let data;
      try {
        data = new FormDataType(form);
      } catch (_) {
        // Let the native POST proceed if the browser cannot prepare an AJAX request.
        return;
      }
      event.preventDefault();
      clearErrors();
      if (honeypot.value.trim()) {
        setStatus('errorHoneypot', 'error');
        return;
      }
      const invalid = validate();
      if (invalid) {
        setStatus('errorValidation', 'error');
        invalid.focus();
        return;
      }

      busy = true;
      button.disabled = true;
      button.textContent = form.dataset.sending || buttonLabel;
      form.setAttribute('aria-busy', 'true');
      setStatus('sending', 'pending');
      try {
        const response = await fetchRequest(form.action, {
          method: 'POST',
          headers: { Accept: 'application/json' },
          body: data
        });
        if (response.ok && !response.redirected) {
          form.reset();
          clearErrors();
          setStatus('success', 'success');
        } else if (response.redirected) {
          setStatus('errorHttp', 'error');
        } else if (response.status === 429) {
          setStatus('errorRate', 'error');
        } else if (response.status === 400 || response.status === 422) {
          let payload = null;
          try { payload = await response.json(); } catch (_) { /* Error bodies may be empty or non-JSON. */ }
          let firstServerField = null;
          if (payload && Array.isArray(payload.errors)) {
            for (const item of payload.errors) {
              const name = item && item.field;
              if (fieldNames.includes(name)) {
                setFieldError(name, 'errorServerField');
                firstServerField ||= fields[name];
              }
            }
          }
          setStatus('errorServerValidation', 'error');
          firstServerField?.focus();
        } else if (response.status === 403) {
          setStatus('errorBlocked', 'error');
        } else {
          setStatus('errorHttp', 'error');
        }
      } catch (_) {
        // Do not log submitted data or error objects to the console.
        setStatus('errorNetwork', 'error');
      } finally {
        busy = false;
        button.disabled = false;
        button.textContent = buttonLabel;
        form.removeAttribute('aria-busy');
      }
    }

    form.addEventListener('invalid', (event) => {
      const name = event.target && event.target.name;
      if (!fieldNames.includes(name)) return;
      const field = fields[name];
      const key = !field.value.trim() ? 'errorRequired'
        : name === 'email' && field.validity.typeMismatch ? 'errorEmail' : 'errorInvalid';
      setFieldError(name, key);
      setStatus('errorValidation', 'error');
    }, true);
    form.addEventListener('submit', handleSubmit);
    form.addEventListener('input', (event) => {
      const name = event.target && event.target.name;
      if (fieldNames.includes(name)) {
        fields[name].removeAttribute('aria-invalid');
        errors[name].textContent = '';
      }
    });
    return { handleSubmit };
  }

  if (typeof document !== 'undefined') {
    const form = document.getElementById('contactForm');
    if (form && typeof window.fetch === 'function' && typeof window.FormData === 'function') {
      setupContactForm(form, window.fetch.bind(window), window.FormData);
    }
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = { setupContactForm };
}());
