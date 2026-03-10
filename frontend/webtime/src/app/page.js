"use client";
import { useState } from "react";
export default function Home() {
  const [domain,setDomain] = useState("");
  const [timeline, setTimeline] = useState([]);
  const[loading,setLoading] = useState(false);

  async function searchTimeline() {
    if(!domain) return;
    setLoading(true);

    try {
      const res = await fetch(`http://localhost:8000/timeline?domain=${domain}`);
      const data = await res.json();

      setTimeline(data.years || {});
    } catch (err) {
      console.log("failed to fetch the website timeline,please try again!!!!!")
    }
    setLoading(false)
  }
  return (
    <main className="min-h-screen p-10 bg-black text-white">
      <h1 className="text-4xl font-bold mb-4">
        Webtime, The Archive of websites
      </h1>
      <p className="text-gray-400 mb-8">
        It shows you the timeline of the website from start till the end
      </p>
      <div className="flex gap-3 mb-10">
        <input
          type="text"
          placeholder="Give your website link here"
          value={domain}
          onChange={(e)=> setDomain(e.target.value)}
          className="px-4 py-2 text-white rounded w-80"
          />
          <button
            onClick={searchTimeline}
            className="bg-blue-600 px-4 py-2 rounded"
            >
              Explore
            </button>

      </div>
      {loading &&<p>Loading timeline(asking aristotle for your websites bro.be patient)</p>}
    <div className="grid grid-cols-4 gap-4">
      {timeline.map((year) =>(
        <div 
          key={year}
          className="bg-gray-900 p-4 rounded hover:bg-gray-800 cursor-pointer">
            {year}
        </div>

      ))}
    </div>
    </main>
  )
}