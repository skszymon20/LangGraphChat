export async function request(path, options = {}) {
    const response = await fetch(path, {
        headers: { "Content-Type": "application/json", ...options.headers },
        ...options,
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || "The request could not be completed.");
    }
    return response.status === 204 ? null : response.json();
}

export const getThreads = () => request("/api/threads");
export const getGeneratingThreads = () => request("/api/threads/generating");
export const getMessages = (threadId) => request(`/api/messages/${threadId}`);
export const deleteThread = (threadId) => request(`/api/threads/${threadId}`, {
    method: "DELETE",
});
export const createThread = (firstMessage, title = null) => request("/api/threads", {
    method: "POST",
    body: JSON.stringify({ first_message: firstMessage, ...(title ? { title } : {}) }),
});
export const sendMessage = (threadId, content) => request("/api/messages", {
    method: "POST",
    body: JSON.stringify({ thread_id: threadId, content }),
});

export function formatDate(value) {
    return new Date(value).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
