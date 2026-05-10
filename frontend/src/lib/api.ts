const LOCAL_IP = "192.168.1.55";

export const getApiBaseUrl = () => {
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    return `http://${host}:8000/api/v1`;
  }
  return `http://${LOCAL_IP}:8000/api/v1`;
};

export const getWsBaseUrl = () => {
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    return `ws://${host}:8000/api/v1/ws/`;
  }
  return `ws://${LOCAL_IP}:8000/api/v1/ws/`;
};


export const api = {
  async get(endpoint: string) {
    const baseUrl = getApiBaseUrl();
    try {
      const response = await fetch(`${baseUrl}${endpoint}`);
      if (!response.ok) throw new Error("API Error");
      return await response.json();
    } catch (error) {
      console.error(`GET ${endpoint} failed:`, error);
      throw error;
    }
  },

  async post(endpoint: string, data?: any) {
    const baseUrl = getApiBaseUrl();
    try {
      const response = await fetch(`${baseUrl}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: data ? JSON.stringify(data) : undefined,
      });
      if (!response.ok) throw new Error("API Error");
      return await response.json();
    } catch (error) {
      console.error(`POST ${endpoint} failed:`, error);
      throw error;
    }
  },

  async delete(endpoint: string) {
    const baseUrl = getApiBaseUrl();
    try {
      const response = await fetch(`${baseUrl}${endpoint}`, {
        method: "DELETE",
      });
      if (!response.ok) throw new Error("API Error");
      
      // Handle cases where the response might be empty (e.g., 204 No Content)
      const text = await response.text();
      return text ? JSON.parse(text) : { success: true };
    } catch (error) {
      console.error(`DELETE ${endpoint} failed:`, error);
      throw error;
    }
  }
};
