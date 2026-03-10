export default function TimelineGrid({years,doamin}) {
    if(!years || years.length === 0) {
        return (
            <p className="text-gray-400">
                No archive found.
            </p>
        );
    }
    return (
        <div className="grid grid-cols-4 gap-4 mt-6">
            {years.map((year) => {
                const snapshotUrl = `https://web.archive.org/web/${year}0101000000/${domain}`;
                return (
                    <a 
                     key={year}
                     href={snapshotUrl}
                     target="_blank"
                     rel="noopener noreferrer"
                     className="bg-gray-900 p-5 rounded hover:bg-800 transition"
                     >
                        <div className="text-2xl font-bold">
                            {year}
                        </div>
                        <p className="text-gray text-sm">
                            View snapshot
                        </p>
                     </a>
                );
            })}
        </div>
    );
}