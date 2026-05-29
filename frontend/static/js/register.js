const WAIVER = [
  {
    id: "risk",
    title: "1. ASSUMPTION OF RISK",
    body: [
      "I understand that participation in martial arts involves physical contact.",
      "I voluntarily assume all risks associated with training."
    ],
  },
  {
    id: "release",
    title: "2. RELEASE OF LIABILITY",
    body: [
      "I release the gym, instructors, and affiliates from all liability.",
      "This includes injury, accident, or loss arising from participation."
    ],
  },
  {
    id: "legal",
    title: "3. MEDIA RELEASE",
    body: [
      "I grant permission for photos and video to be used for marketing."
    ],
  }
];

/* ================= ERROR HELPERS ================= */

function setError(name, message = "required") {
  const el = document.getElementById(`err-${name}`);
  if (!el) return;

  el.innerText = message;
  el.style.color = "red";
  el.style.fontSize = "12px";
}

function clearError(name) {
  const el = document.getElementById(`err-${name}`);
  if (!el) return;

  el.innerText = "";
}

/* ================= CLEAR ALL ERRORS ================= */

function clearAllErrors(form) {
  form.querySelectorAll(".error").forEach(e => (e.innerText = ""));
}

/* ================= WAIVER RENDER ================= */

function renderPage() {
  const container = document.getElementById("waiverPage");

  WAIVER.forEach(section => {
    const div = document.createElement("div");
    div.className = "section";

    div.innerHTML = `
      <h3>${section.title}</h3>
      ${section.body.map(p => `<p>${p}</p>`).join("")}
      <input type="text" name="${section.id}_initials" placeholder="Initials">
      <div id="err-${section.id}_initials" class="error"></div>
    `;

    container.appendChild(div);
  });
}

renderPage();

/* ================= SIGNATURE ================= */

const canvas = document.getElementById("sig");
const ctx = canvas.getContext("2d");

function resizeCanvas() {
  const ratio = window.devicePixelRatio || 1;

  const rect = canvas.getBoundingClientRect();

  // preserve current signature during resize
  const existing = canvas.toDataURL();

  // internal resolution
  canvas.width = rect.width * ratio;
  canvas.height = rect.height * ratio;

  // reset transforms before scaling
  ctx.resetTransform();
  ctx.scale(ratio, ratio);

  // brush styling
  ctx.lineWidth = 2;
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  ctx.strokeStyle = "rgba(0,0,0,0.92)";
  ctx.imageSmoothingEnabled = true;

  // subtle softness
  ctx.shadowBlur = 1;
  ctx.shadowColor = "rgba(0,0,0,0.15)";

  // redraw existing signature
  const img = new Image();

  img.onload = () => {
    ctx.drawImage(
      img,
      0,
      0,
      rect.width,
      rect.height
    );
  };

  img.src = existing;
}

function clearSig() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  ctx.beginPath();
}

resizeCanvas();
window.addEventListener("resize", resizeCanvas);

let drawing = false;

function getXY(e) {
  const rect = canvas.getBoundingClientRect();
  return {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top
  };
}

canvas.addEventListener("pointerdown", (e) => {
  drawing = true;
  const pos = getXY(e);
  ctx.beginPath();
  ctx.moveTo(pos.x, pos.y);
});

canvas.addEventListener("pointermove", (e) => {
  if (!drawing) return;
  e.preventDefault();

  const pos = getXY(e);
  ctx.lineTo(pos.x, pos.y);
  ctx.stroke();
});

window.addEventListener("pointerup", () => {
  drawing = false;
});

function isCanvasBlank(canvas) {
  const blank = document.createElement("canvas");
  blank.width = canvas.width;
  blank.height = canvas.height;
  return canvas.toDataURL() === blank.toDataURL();
}

/* ================= VALIDATION ================= */

function validateForm(form) {
  let valid = true;

  clearAllErrors(form);

  const requiredFields = [
    "first",
    "last",
    "email",
    "phone",
    "password",
    "birthdate",
    "address_1",
    "city",
    "state",
    "zipcode",
    "profile_picture",
    "emergency_contact_name",
    "emergency_contact_relationship",
    "emergency_contact_phone",
    "sign_date"
  ];

  /* TEXT INPUTS */
  requiredFields.forEach(name => {
    const input = form.querySelector(`[name="${name}"]`);

    if (!input || input.disabled) return;

    const value =
      input.disabled
        ? true
        : input.type === "file"
          ? input.files?.length
          : input.value?.trim();

    if (!value) {
      setError(name, "required");
      valid = false;
    } else {
      clearError(name);
    }
  });

  /* WAIVER INITIALS */
  WAIVER.forEach(section => {
    const name = `${section.id}_initials`;
    const input = form.querySelector(`[name="${name}"]`);

    if (!input?.value.trim()) {
      setError(name, "required");
      valid = false;
    } else {
      clearError(name);
    }
  });

  /* SIGNATURE */
  if (isCanvasBlank(canvas)) {
    setError("sig", "required");
    valid = false;
  } else {
    clearError("sig");
  }

  return valid;
}

const profileInput = document.getElementById("profile_picture");
const previewImg = document.getElementById("photoPreview");

profileInput.addEventListener("change", (e) => {
  const file = e.target.files?.[0];

  if (!file) {
    previewImg.src = "";
    previewImg.style.display = "none";
    return;
  }

  const reader = new FileReader();

  reader.onload = (event) => {
    previewImg.src = event.target.result;
    previewImg.style.display = "block";
  };

  reader.readAsDataURL(file);
});

/* ================= PDF BUILD ================= */

async function buildWaiverPDF(signatureBlob) {
  const { jsPDF } = window.jspdf;
  const pdf = new jsPDF();

  let y = 20;

  pdf.setFontSize(16);
  pdf.text("WAIVER AGREEMENT", 20, y);
  y += 10;

  pdf.setFontSize(11);

  for (const section of WAIVER) {
    const initials =
      document.querySelector(`[name="${section.id}_initials"]`)?.value || "";

    pdf.setFont(undefined, "bold");
    pdf.text(section.title, 20, y);
    y += 6;

    pdf.setFont(undefined, "normal");

    for (const line of section.body) {
      const wrapped = pdf.splitTextToSize(line, 170);
      pdf.text(wrapped, 20, y);
      y += wrapped.length * 5;
    }

    pdf.text(`Initials: ${initials}`, 20, y);
    y += 10;
  }

  const sigData = await new Promise(resolve => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.readAsDataURL(signatureBlob);
  });

  pdf.addPage();
  pdf.text("Signature", 20, 20);
  pdf.addImage(sigData, "PNG", 20, 30, 160, 60);

  return pdf.output("blob");
}

/* ================= SUBMIT ================= */

function initRegistrationForm() {
  const form = document.getElementById("form");
  const submitBtn = form?.querySelector('button[type="submit"]');

  if (!form || !submitBtn) return;

  function updateSubmitState() {
    const isValid = validateForm(form);

    submitBtn.disabled = !isValid;
    submitBtn.style.opacity = isValid ? "1" : "0.5";
    submitBtn.style.cursor = isValid ? "pointer" : "not-allowed";
  }

  async function handleSubmit(e) {
    e.preventDefault();

    if (!validateForm(form)) {
      updateSubmitState();
      alert("Please complete all required fields");
      return;
    }

    submitBtn.disabled = true;

    try {
      const sigBlob = await new Promise(resolve =>
        canvas.toBlob(resolve, "image/png")
      );

      const pdfBlob = await buildWaiverPDF(sigBlob);

      const formData = new FormData(form);
      formData.append("waiver_pdf", pdfBlob, "waiver.pdf");
      formData.append("signature_image", sigBlob, "signature.png");

      const res = await fetch("/register", {
        method: "POST",
        body: formData,
      });

      if (res.redirected) {
        window.location.href = res.url;
        return;
      }

      if (!res.ok) {
        alert(data.detail || "Registration failed");
        return;
      }

      window.location.href = "/signin";

    } catch (err) {
      console.error(err);
      alert("Unexpected error occurred");
    } finally {
      updateSubmitState();
    }
  }

  form.addEventListener("input", updateSubmitState);
  form.addEventListener("change", updateSubmitState);
  form.addEventListener("submit", handleSubmit);

  updateSubmitState();
}

document.addEventListener("DOMContentLoaded", initRegistrationForm);

