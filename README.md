# 오늘의 운세 🔮

Next.js(App Router)로 만든 '오늘의 운세' 사이트입니다. 버튼을 누르면 카드가 3D로 뒤집히며
랜덤 운세 등급, 애정·금전·직업운, 그리고 행운의 아이템/색/숫자가 나타납니다.

## 실행 방법

```bash
npm install
npm run dev
```

이후 브라우저에서 http://localhost:3000 접속.

## 구조

- `app/page.js` — 카드 뒤집기 인터랙션 (클라이언트 컴포넌트)
- `app/fortunes.js` — 운세·행운 아이템 데이터
- `app/page.module.css` — 카드 3D 플립 애니메이션 스타일
- `app/globals.css` — 전역 배경/폰트
