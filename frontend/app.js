/**
 * SupportPilot 前端 — SSE 流式对话 + 文件上传
 */

const chatHistory = document.getElementById("chat-history");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const fileInput = document.getElementById("file-input");
const uploadStatus = document.getElementById("upload-status");

// ── 发送消息 ──

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    // 显示用户消息
    appendMessage("user", message);
    userInput.value = "";
    sendBtn.disabled = true;

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message }),
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        // 读取 SSE 流
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop(); // 保留不完整的行

            let currentEvent = "";
            for (const line of lines) {
                if (line.startsWith("event: ")) {
                    currentEvent = line.slice(7).trim();
                } else if (line.startsWith("data: ")) {
                    const dataStr = line.slice(6);
                    handleSSEEvent(currentEvent, dataStr);
                }
            }
        }
    } catch (err) {
        appendMessage("error", `请求失败: ${err.message}`);
    } finally {
        sendBtn.disabled = false;
    }
}

// ── 处理 SSE 事件 ──

function handleSSEEvent(event, dataStr) {
    let data;
    try {
        data = JSON.parse(dataStr);
    } catch {
        data = { output: dataStr };
    }

    switch (event) {
        case "action":
            appendMessage("action", `🔧 调用工具: ${data.tool}\n输入: ${typeof data.input === "object" ? JSON.stringify(data.input) : data.input}`);
            break;
        case "observation":
            appendMessage("observation", `📋 工具结果:\n${truncate(data.output, 500)}`);
            break;
        case "answer":
            appendMessage("assistant", data.output);
            break;
        case "error":
            appendMessage("error", `❌ 错误: ${data.message || dataStr}`);
            break;
        case "done":
            // 对话结束
            break;
        default:
            // 忽略未知事件
            break;
    }
}

// ── DOM 操作 ──

function appendMessage(type, content) {
    const div = document.createElement("div");
    div.className = `message ${type}`;
    div.textContent = content;
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function truncate(str, maxLen) {
    if (!str) return "";
    return str.length > maxLen ? str.slice(0, maxLen) + "..." : str;
}

// ── 文件上传 ──

fileInput.addEventListener("change", async () => {
    const file = fileInput.files[0];
    if (!file) return;

    uploadStatus.textContent = "上传中...";
    uploadStatus.className = "";

    const formData = new FormData();
    formData.append("file", file);

    try {
        const resp = await fetch("/upload", { method: "POST", body: formData });
        const result = await resp.json();

        if (resp.ok) {
            uploadStatus.textContent = `✅ ${result.filename} — ${result.chunks} 个分块已索引`;
            uploadStatus.className = "success";
        } else {
            uploadStatus.textContent = `❌ ${result.detail || "上传失败"}`;
            uploadStatus.className = "error";
        }
    } catch (err) {
        uploadStatus.textContent = `❌ 网络错误: ${err.message}`;
        uploadStatus.className = "error";
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
