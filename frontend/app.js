/**
 * SupportPilot 前端 — SSE token 级流式对话 + 文件上传
 */

const chatHistory = document.getElementById("chat-history");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const fileInput = document.getElementById("file-input");
const uploadStatus = document.getElementById("upload-status");

// 会话 ID（随机生成，刷新页面重置）
const sessionId = "session-" + Math.random().toString(36).slice(2, 10);

// 当前流式输出的元素
let streamingDiv = null;

// 用户是否手动滚动过（一旦手动滚动，停止自动滚动）
let userScrolled = false;

// 监听用户手动滚动
chatHistory.addEventListener("scroll", () => {
    // 如果用户滚动到距离底部 50px 以内，恢复自动滚动
    if (isNearBottom(50)) {
        userScrolled = false;
    }
});

// 判断是否在底部
function isNearBottom(threshold = 100) {
    return chatHistory.scrollTop + chatHistory.clientHeight >= chatHistory.scrollHeight - threshold;
}

// 智能滚动：只在用户没有手动滚动时自动滚动
function autoScroll() {
    if (!userScrolled) {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
}

// 用户开始输入时重置滚动状态
function resetScrollState() {
    userScrolled = false;
}

// 监听用户拖动滚动条
let scrollTimer = null;
chatHistory.addEventListener("mousedown", () => {
    // 用户点击滚动区域时，标记为手动滚动
    scrollTimer = setTimeout(() => {
        userScrolled = true;
    }, 200);
});
chatHistory.addEventListener("mouseup", () => {
    clearTimeout(scrollTimer);
});

// ── 发送消息 ──

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    resetScrollState(); // 发送消息时重置滚动状态
    appendMessage("user", message);
    userInput.value = "";
    sendBtn.disabled = true;
    streamingDiv = null;

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message, session_id: sessionId }),
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop();

            let currentEvent = "";
            for (const line of lines) {
                if (line.startsWith("event: ")) {
                    currentEvent = line.slice(7).trim();
                } else if (line.startsWith("data: ")) {
                    handleSSEEvent(currentEvent, line.slice(6));
                }
            }
        }
    } catch (err) {
        appendMessage("error", `请求失败: ${err.message}`);
    } finally {
        sendBtn.disabled = false;
        streamingDiv = null;
    }
}

// ── 处理 SSE 事件 ──

function handleSSEEvent(event, dataStr) {
    let data;
    try { data = JSON.parse(dataStr); } catch { data = { output: dataStr }; }

    switch (event) {
        case "token":
            if (!streamingDiv) {
                streamingDiv = appendMessage("assistant", "");
            }
            streamingDiv.textContent += data.content;
            autoScroll(); // 智能滚动
            break;

        case "action":
            closeStreamingDiv();
            appendMessage("action", `🔧 调用工具: ${data.tool}\n输入: ${typeof data.input === "object" ? JSON.stringify(data.input) : data.input}`);
            break;

        case "observation":
            appendMessage("observation", `📋 工具结果:\n${truncate(data.output, 500)}`);
            break;

        case "answer":
            if (!streamingDiv || streamingDiv.textContent.trim() === "") {
                closeStreamingDiv();
                appendMessage("assistant", data.output);
            } else {
                closeStreamingDiv();
            }
            break;

        case "error":
            closeStreamingDiv();
            appendMessage("error", `❌ 错误: ${data.message || dataStr}`);
            break;

        case "done":
            closeStreamingDiv();
            break;
    }
}

function closeStreamingDiv() {
    streamingDiv = null;
}

// ── DOM 操作 ──

function appendMessage(type, content) {
    const div = document.createElement("div");
    div.className = `message ${type}`;
    div.textContent = content;
    chatHistory.appendChild(div);
    autoScroll(); // 智能滚动
    return div;
}

function truncate(str, maxLen) {
    if (!str) return "";
    return str.length > maxLen ? str.slice(0, maxLen) + "..." : str;
}

// ── 文件上传 ──

function showUploadStatus(text, type) {
    uploadStatus.textContent = text;
    uploadStatus.className = type;
    // 5 秒后自动隐藏
    setTimeout(() => {
        uploadStatus.textContent = "";
        uploadStatus.className = "";
    }, 5000);
}

fileInput.addEventListener("change", async () => {
    const file = fileInput.files[0];
    if (!file) return;

    showUploadStatus("上传中...", "");

    const formData = new FormData();
    formData.append("file", file);

    try {
        const resp = await fetch("/upload", { method: "POST", body: formData });
        const result = await resp.json();

        if (resp.ok) {
            showUploadStatus(`✅ ${result.filename} — ${result.chunks} 个分块已索引`, "success");
        } else {
            showUploadStatus(`❌ ${result.detail || "上传失败"}`, "error");
        }
    } catch (err) {
        showUploadStatus(`❌ 网络错误: ${err.message}`, "error");
    }

    fileInput.value = "";
});

// ── 快捷键 ──

userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// ── 文档管理 ──

let docPanelVisible = false;

function toggleDocPanel() {
    const panel = document.getElementById("doc-panel");
    docPanelVisible = !docPanelVisible;
    panel.style.display = docPanelVisible ? "block" : "none";
    if (docPanelVisible) loadDocuments();
}

async function loadDocuments() {
    const list = document.getElementById("doc-list");
    list.innerHTML = '<div class="doc-empty">加载中...</div>';

    try {
        const resp = await fetch("/documents");
        const data = await resp.json();

        if (!data.documents || data.documents.length === 0) {
            list.innerHTML = '<div class="doc-empty">暂无文档，请上传</div>';
            return;
        }

        list.innerHTML = data.documents.map(doc => `
            <div class="doc-item">
                <span class="doc-name" title="${doc.source}">📄 ${doc.filename}</span>
                <span class="doc-meta">${doc.chunks} 块</span>
                <button class="doc-delete" onclick="deleteDocument('${doc.doc_id}')" title="删除">🗑️</button>
            </div>
        `).join("");
    } catch (err) {
        list.innerHTML = `<div class="doc-empty">加载失败: ${err.message}</div>`;
    }
}

async function deleteDocument(docId) {
    if (!confirm(`确定删除文档 ${docId}？`)) return;

    try {
        const resp = await fetch(`/documents/${docId}`, { method: "DELETE" });
        const data = await resp.json();

        if (resp.ok) {
            loadDocuments();
        } else {
            alert(`删除失败: ${data.detail || "未知错误"}`);
        }
    } catch (err) {
        alert(`删除失败: ${err.message}`);
    }
}

// ── 历史管理 ──

async function clearHistory() {
    if (!confirm("确定清除当前对话历史？")) return;

    try {
        await fetch(`/history/${sessionId}`, { method: "DELETE" });
        const messages = chatHistory.querySelectorAll(".message:not(.system)");
        messages.forEach(m => m.remove());
    } catch (err) {
        alert(`清除失败: ${err.message}`);
    }
}
