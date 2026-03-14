import Link from "next/link";

export default function AboutPage() {
    return (
        <main className="mx-auto w-full max-w-270 px-6 py-8 text-[#e8e7e3] font-mono">
            <h1 className="mt-4 text-3xl font-bold">About This Project</h1>
            <p className="mt-4 text-lg">
                This project is a personal initiative to explore and visualize the history of websites using the Internet Archive's Wayback Machine. It allows users to see how a website has evolved over time by displaying snapshots taken at different points in history.
            </p>
            <p> yeah i get it the site is a bit slow but i cant do anything about it so yeah </p>
            <p className="mt-4 text-lg">
                The frontend is built with Next.js, while the backend is powered by FastAPI. The application fetches data from the Wayback Machine API and presents it in an interactive timeline format.
            </p>
            <p className="mt-4 text-lg">
                If you're interested in contributing or have any questions, feel free to check out the <Link href="https://github.com/praneet1503/website-timeline" className="text-blue-500 hover:underline">GitHub repository</Link>.
            </p>
            <p>the website is built with Next.js and styled with Tailwind CSS.</p>
            <p> the text is jetbrains mono if you the like text.(i liked it obv so much)</p>
            <p>and if you have any suggestions on improving the wbeiste just hit me up <a href="https://hackclub.enterprise.slack.com/team/U07V12XBSF6" className="text-blue-500 hover:underline">on Slack</a></p>
        </main>
    );
}
