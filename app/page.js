"use client";

import { useState } from "react";
import { fortunes, luckyItems, luckyColors } from "./fortunes";
import styles from "./page.module.css";

function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

export default function Home() {
  const [flipped, setFlipped] = useState(false);
  const [result, setResult] = useState(null);

  function draw() {
    if (flipped) {
      // 다시 뽑기: 먼저 카드를 닫았다가 새 운세로 다시 연다
      setFlipped(false);
      setTimeout(() => {
        setResult(buildResult());
        setFlipped(true);
      }, 450);
      return;
    }
    setResult(buildResult());
    setFlipped(true);
  }

  function buildResult() {
    return {
      fortune: pick(fortunes),
      item: pick(luckyItems),
      color: pick(luckyColors),
      number: Math.floor(Math.random() * 45) + 1,
    };
  }

  const today = new Date().toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "long",
  });

  return (
    <main className={styles.main}>
      <div className={styles.header}>
        <p className={styles.date}>{today}</p>
        <h1 className={styles.title}>오늘의 운세</h1>
        <p className={styles.subtitle}>카드를 뒤집어 오늘의 기운을 확인하세요</p>
      </div>

      <div className={styles.scene}>
        <div
          className={`${styles.card} ${flipped ? styles.isFlipped : ""}`}
          onClick={draw}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && draw()}
        >
          {/* 카드 뒷면 (처음 보이는 면) */}
          <div className={`${styles.face} ${styles.back}`}>
            <div className={styles.backPattern}>
              <span className={styles.backEmoji}>🔮</span>
              <span className={styles.backText}>TAP TO REVEAL</span>
            </div>
          </div>

          {/* 카드 앞면 (운세 결과) */}
          <div className={`${styles.face} ${styles.front}`}>
            {result && (
              <div className={styles.result}>
                <div className={styles.grade}>
                  <span className={styles.gradeEmoji}>{result.fortune.emoji}</span>
                  <span className={styles.gradeText}>{result.fortune.grade}</span>
                </div>
                <p className={styles.message}>{result.fortune.message}</p>

                <div className={styles.aspects}>
                  <div className={styles.aspect}>
                    <span className={styles.aspectlabel}>💕 애정</span>
                    <span>{result.fortune.love}</span>
                  </div>
                  <div className={styles.aspect}>
                    <span className={styles.aspectlabel}>💰 금전</span>
                    <span>{result.fortune.money}</span>
                  </div>
                  <div className={styles.aspect}>
                    <span className={styles.aspectlabel}>💼 직업</span>
                    <span>{result.fortune.work}</span>
                  </div>
                </div>

                <div className={styles.lucky}>
                  <div className={styles.luckyRow}>
                    <span className={styles.luckyKey}>행운의 아이템</span>
                    <span className={styles.luckyVal}>{result.item}</span>
                  </div>
                  <div className={styles.luckyRow}>
                    <span className={styles.luckyKey}>행운의 색</span>
                    <span className={styles.luckyVal}>
                      <span
                        className={styles.swatch}
                        style={{ background: result.color.hex }}
                      />
                      {result.color.name}
                    </span>
                  </div>
                  <div className={styles.luckyRow}>
                    <span className={styles.luckyKey}>행운의 숫자</span>
                    <span className={styles.luckyVal}>{result.number}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <button className={styles.button} onClick={draw}>
        {flipped ? "🔄 다시 뽑기" : "🃏 운세 뽑기"}
      </button>
    </main>
  );
}
