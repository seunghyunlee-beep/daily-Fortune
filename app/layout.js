import "./globals.css";

export const metadata = {
  title: "오늘의 운세 🔮",
  description: "카드를 뒤집어 오늘의 운세와 행운의 아이템을 확인하세요",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
