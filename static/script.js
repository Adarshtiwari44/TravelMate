let currentThreadId = localStorage.getItem("travel_thread_id") || null;
let latestAnswerMarkdown = "";

function setPrompt(text) {
    const input = document.getElementById("userInput");
    input.value = text;
    input.focus();
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 120) + "px";
}

function setLoading(isLoading) {
    const sendBtn = document.getElementById("sendBtn");
    const btnText = document.getElementById("btnText");
    const btnLoader = document.getElementById("btnLoader");

    sendBtn.disabled = isLoading;

    if (isLoading) {
        btnText.classList.add("hidden");
        btnLoader.classList.remove("hidden");
    } else {
        btnText.classList.remove("hidden");
        btnLoader.classList.add("hidden");
    }
}

function showError(message) {
    const errorBox = document.getElementById("errorBox");
    errorBox.textContent = message;
    errorBox.classList.remove("hidden");
    errorBox.scrollIntoView({ behavior: "smooth", block: "center" });
}

function hideError() {
    const errorBox = document.getElementById("errorBox");
    errorBox.classList.add("hidden");
    errorBox.textContent = "";
}

function wrapMarkdownTables(root) {
    if (!root) return;

    const tables = root.querySelectorAll("table");

    tables.forEach((table) => {
        if (table.parentElement && table.parentElement.classList.contains("result-table-wrapper")) {
            return;
        }

        const wrapper = document.createElement("div");
        wrapper.className = "result-table-wrapper";

        if (table.parentNode) {
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }
    });
}

function showResult(answer, threadId) {
    latestAnswerMarkdown = answer;

    const resultSection = document.getElementById("resultSection");
    const resultBox = document.getElementById("resultBox");
    const threadInfo = document.getElementById("threadInfo");

    if (typeof marked !== "undefined") {
        resultBox.innerHTML = marked.parse(answer);
        wrapMarkdownTables(resultBox);
    } else {
        resultBox.innerText = answer;
    }

    threadInfo.textContent = `Thread ID: ${threadId}`;
    resultSection.classList.remove("hidden");

    resultSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}

async function sendMessage() {
    hideError();

    const input = document.getElementById("userInput");
    const message = input.value.trim();

    if (!message) {
        showError("Please enter your travel request first.");
        input.focus();
        return;
    }

    setLoading(true);

    try {
        const response = await fetch("/api/travel", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message,
                thread_id: currentThreadId
            })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Something went wrong.");
        }

        currentThreadId = data.thread_id;
        localStorage.setItem("travel_thread_id", currentThreadId);

        showResult(data.answer, data.thread_id);
    } catch (error) {
        showError(error.message || "Unable to generate the travel plan.");
    } finally {
        setLoading(false);
    }
}

function copyResult() {
    const resultBox = document.getElementById("resultBox");
    const text = resultBox.innerText;

    if (!text) return;

    navigator.clipboard.writeText(text)
        .then(() => {
            const copyBtn = document.querySelector(".copy-btn");
            const oldText = copyBtn.textContent;
            copyBtn.textContent = "Copied!";

            setTimeout(() => {
                copyBtn.textContent = oldText;
            }, 1400);
        })
        .catch(() => {
            showError("Could not copy result.");
        });
}

function downloadPDF() {
    const pdfContent = document.getElementById("pdfContent");

    if (!latestAnswerMarkdown || !pdfContent) {
        showError("No travel plan available to download.");
        return;
    }

    const downloadBtn = document.querySelector(".download-btn");
    const oldText = downloadBtn.textContent;

    downloadBtn.textContent = "Preparing PDF...";
    downloadBtn.disabled = true;

    const options = {
        margin: 0.5,
        filename: "tripmate-ai-travel-plan.pdf",
        image: {
            type: "jpeg",
            quality: 0.98
        },
        html2canvas: {
            scale: 2,
            useCORS: true,
            backgroundColor: "#ffffff"
        },
        jsPDF: {
            unit: "in",
            format: "a4",
            orientation: "portrait"
        },
        pagebreak: {
            mode: ["avoid-all", "css", "legacy"]
        }
    };

    html2pdf()
        .set(options)
        .from(pdfContent)
        .save()
        .then(() => {
            downloadBtn.textContent = oldText;
            downloadBtn.disabled = false;
        })
        .catch(() => {
            downloadBtn.textContent = oldText;
            downloadBtn.disabled = false;
            showError("Could not download PDF.");
        });
}

const input = document.getElementById("userInput");

input.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = Math.min(this.scrollHeight, 120) + "px";
});

input.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

document.addEventListener("keydown", function (event) {
    if (event.ctrlKey && event.key === "Enter") {
        sendMessage();
    }
});
function startPlanning() {
    const planner = document.getElementById("planner");
    const input = document.getElementById("userInput");

    if (planner) {
        planner.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });
    }

    setTimeout(() => {
        if (input) {
            input.focus();
        }
    }, 500);
}