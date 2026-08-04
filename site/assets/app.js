const copyButton = document.querySelector("[data-copy-url]");
const toast = document.querySelector("[data-toast]");
let toastTimer;

function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("visible");
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toast.classList.remove("visible"), 2200);
}

async function copyImportUrl() {
  const url = copyButton?.dataset.copyUrl;
  if (!url) return;

  try {
    await navigator.clipboard.writeText(url);
    showToast("导入链接已复制");
  } catch {
    window.prompt("复制下面的导入链接", url);
  }
}

copyButton?.addEventListener("click", copyImportUrl);
