const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
//fetching the data for domain :/
export async function fetchTimeline(domain) {

    if (!domain) {
        throw new Error("Domain is required");
    }
    const url = `${API_BASE}/timeline?domain=${encodeURIComponent(domain)}}`

    try {

        const res = await fetch(url, {
            method:"GET",
            headers:{
                "Content-Type":"application/json",
            },
            cache:"no-store"
        });

        if(!res.ok) {
            throw new error(`Backend error ${res.status}`);
        }
        const data = await res.json();
        return data;
    } catch(error) {
        console.error("Timeline API failed:",error);
        return{
            domain,
            years:[],
            error:"Failed to load timeline"
        };
    }
}