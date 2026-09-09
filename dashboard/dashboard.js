(function () {
  const D = window.DASHBOARD_DATA;

  function pct(x, digits) {
    if (x === null || x === undefined) return "N/A";
    return (x * 100).toFixed(digits === undefined ? 1 : digits) + "%";
  }
  function num(x, digits) {
    if (x === null || x === undefined) return "N/A";
    return x.toFixed(digits === undefined ? 3 : digits);
  }
  function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  // ---- Overview stat row already static; nothing dynamic needed there ----

  // ---- Dataset: population funnel ----
  (function () {
    const table = document.getElementById("funnel-table");
    const rows = D.population_funnel;
    let html = "<thead><tr><th>Stage</th><th class=\"num\">Samples</th></tr></thead><tbody>";
    rows.forEach((r) => {
      html += `<tr><td>${r.stage}</td><td class="num">${r.n}</td></tr>`;
    });
    html += "</tbody>";
    table.innerHTML = html;
  })();

  // ---- Dataset: class distribution chart ----
  (function () {
    const container = document.getElementById("class-dist-chart");
    const classes = D.class_distribution.final_classes;
    const max = Math.max(...Object.values(classes));
    let html = "";
    Object.entries(classes).forEach(([name, n]) => {
      const w = Math.round((n / max) * 100);
      html += `
        <div class="bar-item">
          <div>${name}</div>
          <div class="bar-track"><div class="bar-fill arcface" style="width:${w}%"></div></div>
          <div class="bar-val">${n}</div>
        </div>`;
    });
    container.innerHTML = html;
  })();

  // ---- Baseline: historical + common subset ----
  (function () {
    const h = D.historical;
    setText("hist-acc", pct(h.accuracy));
    setText("hist-fa", pct(h.false_angry_rate));
    setText("hist-na", `${h.neutral_to_angry_count}/${h.neutral_to_angry_total} (${pct(h.neutral_to_angry_rate)})`);

    const c = D.common_subset;
    setText("common-hse-acc", pct(c.hsemotion.accuracy));
    setText("common-hse-p", pct(c.hsemotion.macro_precision));
    setText("common-hse-r", pct(c.hsemotion.macro_recall));
    setText("common-hse-f1", pct(c.hsemotion.macro_f1));
  })();

  // ---- ArcFace section ----
  (function () {
    const a = D.common_subset.arcface;
    setText("af-acc", pct(a.accuracy));
    setText("af-p", pct(a.macro_precision));
    setText("af-r", pct(a.macro_recall));
    setText("af-f1", pct(a.macro_f1));
  })();

  // ---- Comparison table ----
  (function () {
    const c = D.common_subset;
    const tbody = document.getElementById("comparison-table");
    const rows = [
      ["Accuracy", c.arcface.accuracy, c.hsemotion.accuracy],
      ["Macro Precision", c.arcface.macro_precision, c.hsemotion.macro_precision],
      ["Macro Recall", c.arcface.macro_recall, c.hsemotion.macro_recall],
      ["Macro F1", c.arcface.macro_f1, c.hsemotion.macro_f1],
    ];
    tbody.innerHTML = rows
      .map(
        (r) =>
          `<tr><td>${r[0]}</td><td class="num row-arcface">${pct(r[1])}</td><td class="num row-hsemotion">${pct(r[2])}</td></tr>`
      )
      .join("");

    const p = D.statistics.mcnemar.p_value;
    setText("mcnemar-p", num(p, 4));
    setText("mcnemar-p-2", num(p, 4));
    setText("mcnemar-p-3", num(p, 4));
  })();

  // ---- Error rate chart (overall_error_by_model) ----
  (function () {
    const container = document.getElementById("error-rate-chart");
    const af = D.overall_error_by_model["ArcFace+LR"] || D.overall_error_by_model["ArcFace"] || [];
    const hse = D.overall_error_by_model["HSEmotion"] || [];
    const byClass = {};
    af.forEach((r) => {
      byClass[r.ground_truth] = byClass[r.ground_truth] || {};
      byClass[r.ground_truth].arcface = r.error_rate;
    });
    hse.forEach((r) => {
      byClass[r.ground_truth] = byClass[r.ground_truth] || {};
      byClass[r.ground_truth].hsemotion = r.error_rate;
    });
    let html = "";
    Object.entries(byClass).forEach(([name, v]) => {
      html += `
        <div class="bar-item">
          <div>${name}</div>
          <div>
            <div class="bar-track" style="margin-bottom:4px;"><div class="bar-fill arcface" style="width:${(v.arcface || 0) * 100}%"></div></div>
            <div class="bar-track"><div class="bar-fill hsemotion" style="width:${(v.hsemotion || 0) * 100}%"></div></div>
          </div>
          <div class="bar-val">${pct(v.arcface)} / ${pct(v.hsemotion)}</div>
        </div>`;
    });
    container.innerHTML = html;
  })();

  // ---- Neutral analysis ----
  (function () {
    const n = D.neutral_analysis;
    setText("neu-af-n", n.arcface.n);
    setText("neu-af-correct", n.arcface.correct);
    setText("neu-af-err", pct(n.arcface.error_rate));
    setText("neu-af-dom", `${n.arcface.dominant_wrong_class} (${n.arcface.dominant_wrong_count})`);

    setText("neu-hse-n", n.hsemotion.n);
    setText("neu-hse-correct", n.hsemotion.correct);
    setText("neu-hse-err", pct(n.hsemotion.error_rate));
    setText("neu-hse-dom", `${n.hsemotion.dominant_wrong_class} (${n.hsemotion.dominant_wrong_count})`);
    setText(
      "neu-hse-angry",
      `${n.hsemotion.neutral_to_angry_count}/${n.hsemotion.n} (${pct(n.hsemotion.neutral_to_angry_rate)})`
    );
  })();

  // ---- Skin tone population table ----
  (function () {
    const table = document.getElementById("skin-tone-pop-table");
    let html = "<thead><tr><th>Skin Tone</th><th class=\"num\">N</th><th class=\"num\">ArcFace Acc.</th><th class=\"num\">HSEmotion Acc.</th></tr></thead><tbody>";
    D.skin_tone.forEach((r) => {
      const isUnknown = r.skin_tone.toLowerCase() === "unknown";
      html += `<tr>
        <td>${r.skin_tone}${isUnknown ? ' <span class="badge gray">excluded from accuracy comparison</span>' : ""}</td>
        <td class="num">${r.n}</td>
        <td class="num">${r.arcface_accuracy === null ? '<span class="na">N/A</span>' : pct(r.arcface_accuracy)}</td>
        <td class="num">${r.hsemotion_accuracy === null ? '<span class="na">N/A</span>' : pct(r.hsemotion_accuracy)}</td>
      </tr>`;
    });
    html += "</tbody>";
    table.innerHTML = html;
  })();

  // ---- Statistical evidence: bootstrap CIs ----
  (function () {
    function parseCI(s) {
      // stored as a Python tuple string, e.g. "(0.4074, 0.3383, 0.4809)"
      const parts = s.replace(/[()]/g, "").split(",").map(Number);
      return { point: parts[0], lower: parts[1], upper: parts[2] };
    }
    const af = parseCI(D.statistics.bootstrap_accuracy_arcface);
    const hse = parseCI(D.statistics.bootstrap_accuracy_hsemotion);
    setText("ci-af", `${pct(af.point)} [${pct(af.lower)} – ${pct(af.upper)}]`);
    setText("ci-hse", `${pct(hse.point)} [${pct(hse.lower)} – ${pct(hse.upper)}]`);
  })();

  // ---- Findings table ----
  (function () {
    const tbody = document.querySelector("#findings-table tbody");
    if (!tbody || !D.findings) return;
    tbody.innerHTML = D.findings
      .map((r) => {
        const evidence = `${r.metric || ""} (${r.population || ""})`;
        return `<tr><td>${r.finding || ""}</td><td>${evidence}</td><td>${r.evidence_strength || ""}</td></tr>`;
      })
      .join("");
  })();

  // ---- Limitations table ----
  (function () {
    const tbody = document.querySelector("#limitations-table tbody");
    if (!tbody || !D.limitations) return;
    tbody.innerHTML = D.limitations
      .map((r) => `<tr><td>${r.limitation || ""}</td><td>${r.impact || ""}</td></tr>`)
      .join("");
  })();

  // ---- Scroll-spy nav highlighting ----
  (function () {
    const links = Array.from(document.querySelectorAll("nav.side a"));
    const sections = links
      .map((l) => document.querySelector(l.getAttribute("href")))
      .filter(Boolean);
    function onScroll() {
      let current = sections[0];
      sections.forEach((s) => {
        if (s.getBoundingClientRect().top - 80 <= 0) current = s;
      });
      links.forEach((l) => l.classList.toggle("active", l.getAttribute("href") === "#" + current.id));
    }
    document.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  })();
})();
