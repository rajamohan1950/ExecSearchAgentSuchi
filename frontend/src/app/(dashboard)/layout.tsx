import NavBar from "@/components/nav-bar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </div>
  );
}
