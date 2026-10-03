(() => {
  const qs = (selector, root = document) => root.querySelector(selector);
  const qsa = (selector, root = document) => [...root.querySelectorAll(selector)];

  qsa('[data-time]').forEach((node) => {
    node.textContent = new Intl.DateTimeFormat('zh-CN', {
      hour: '2-digit', minute: '2-digit', hour12: false
    }).format(new Date());
  });

  qsa('[data-choice-group]').forEach((group) => {
    const choices = qsa('[data-choice]', group);
    const phone = group.closest('.phone');
    const submit = phone ? qs('[data-submit-quiz]', phone) : null;
    choices.forEach((choice) => {
      choice.addEventListener('click', () => {
        if (choice.disabled) return;
        choices.forEach((item) => item.setAttribute('aria-pressed', 'false'));
        choice.setAttribute('aria-pressed', 'true');
        if (submit) submit.disabled = false;
      });
    });
  });

  qsa('[data-submit-quiz]').forEach((button) => {
    button.addEventListener('click', () => {
      const phone = button.closest('.phone');
      const selected = qs('[data-choice][aria-pressed="true"]', phone);
      const feedback = qs('.answer-feedback', phone);
      if (!selected || !feedback) return;
      qsa('[data-choice]', phone).forEach((choice) => {
        choice.disabled = true;
        choice.classList.toggle('correct', choice.dataset.correct === 'true');
        choice.classList.toggle('wrong', choice === selected && choice.dataset.correct !== 'true');
        const mark = qs('.choice__mark', choice);
        if (mark && choice.dataset.correct === 'true') mark.textContent = '✓';
        if (mark && choice === selected && choice.dataset.correct !== 'true') mark.textContent = '×';
      });
      feedback.hidden = false;
      button.textContent = '本题已提交';
      button.disabled = true;
      qs('strong', feedback)?.focus?.();
    });
  });

  qsa('[data-toggle]').forEach((button) => {
    button.addEventListener('click', () => {
      const next = button.getAttribute('aria-pressed') !== 'true';
      button.setAttribute('aria-pressed', String(next));
    });
  });

  qsa('[data-tab]').forEach((tab) => {
    tab.addEventListener('click', () => {
      const root = tab.closest('[data-tabs-root]');
      if (!root) return;
      qsa('[data-tab]', root).forEach((item) => item.setAttribute('aria-selected', 'false'));
      qsa('.tab-panel', root).forEach((panel) => { panel.hidden = true; });
      tab.setAttribute('aria-selected', 'true');
      const panel = qs(`#${tab.dataset.tab}`, root);
      if (panel) panel.hidden = false;
    });
  });

  qsa('[data-clear-search]').forEach((button) => {
    button.addEventListener('click', () => {
      const input = qs('input', button.closest('.search-wrap'));
      if (!input) return;
      input.value = '';
      input.focus();
      button.hidden = true;
    });
    const input = qs('input', button.closest('.search-wrap'));
    input?.addEventListener('input', () => { button.hidden = !input.value; });
  });

  qsa('[data-open-dialog]').forEach((button) => {
    button.addEventListener('click', () => {
      const dialog = document.getElementById(button.dataset.openDialog);
      if (!dialog) return;
      dialog.dataset.returnFocus = button.id || '';
      dialog.showModal();
      qs('[data-dialog-cancel]', dialog)?.focus();
    });
  });

  qsa('dialog').forEach((dialog) => {
    qsa('[data-dialog-close]', dialog).forEach((button) => {
      button.addEventListener('click', () => dialog.close());
    });
    dialog.addEventListener('close', () => {
      const target = dialog.dataset.returnFocus && document.getElementById(dialog.dataset.returnFocus);
      target?.focus();
    });
  });

  const showToast = (phone, message) => {
    const toast = qs('.toast', phone);
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('show');
    window.clearTimeout(toast._timer);
    toast._timer = window.setTimeout(() => toast.classList.remove('show'), 2600);
  };

  window.prototypeAction = (event) => {
    const button = event.currentTarget;
    if (button.matches('[data-choice], [data-tab], [data-toggle], [data-submit-quiz], [data-open-dialog], [data-dialog-close], [data-toast], [data-progress-demo], [data-clear-search]')) return;
    const phone = button.closest('.phone');
    if (phone) showToast(phone, button.getAttribute('aria-label') ? `${button.getAttribute('aria-label')} · 原型动作` : '已触发原型动作');
  };

  qsa('[data-toast]').forEach((button) => {
    button.addEventListener('click', () => showToast(button.closest('.phone'), button.dataset.toast));
  });

  qsa('[data-progress-demo]').forEach((button) => {
    button.addEventListener('click', () => {
      if (button.dataset.running === 'true') return;
      button.dataset.running = 'true';
      button.disabled = true;
      const phone = button.closest('.phone');
      const stages = qsa('.stage', phone);
      let index = stages.findIndex((stage) => stage.classList.contains('current'));
      const advance = () => {
        if (index >= 0) {
          stages[index].classList.remove('current');
          stages[index].classList.add('done');
          const dot = qs('.stage__dot', stages[index]);
          if (dot) dot.textContent = '✓';
        }
        index += 1;
        if (index < stages.length) {
          stages[index].classList.add('current');
          window.setTimeout(advance, 850);
        } else {
          button.textContent = '已通过质量检查';
          showToast(phone, '题目准备好了，进入第一关');
        }
      };
      advance();
    });
  });
})();
