import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "Lab Scan Reader",
  description: "Демо-прототип: чтение сканов лабораторных анализов в карту пациента",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <div className="demo-banner" role="note">
          Демо-прототип. Не медицинское изделие, не для диагностики. Только вымышленные данные.
        </div>
        <main>{children}</main>
      </body>
    </html>
  );
}
