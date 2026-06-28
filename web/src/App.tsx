import Hero from "./components/Hero";
import Reveal from "./components/Reveal";

const balls = [
  {
    color: "#d8493f",
    name: "퀘플 · Quaffle",
    tag: "착하고 둔한 놈",
    body: "선수가 안고 던지는 메인 공. 정전식 터치로 '잡힘'을 인식하면 추력 0 — 손안에서 윙윙대지 않습니다. 던지면 드론이 알아서 포물선을 보정합니다.",
    quip: "\u201c제일 안전해야 하는 공. 손가락 보호 1순위.\u201d",
  },
  {
    color: "#9aa0aa",
    name: "블러저 · Bludger",
    tag: "널 싫어하는 놈",
    body: "쇠공으로 만들면 다 죽습니다. 그래서 검은 에어백 쉘. 라이다 예측회피로 접촉 10cm 직전 급정지. 판정은 물리 충돌이 아니라 근접 판정으로.",
    quip: "\u201c맞으면 안 아픈데 기록상으론 죽는다. 인생 같다.\u201d",
  },
  {
    color: "#f4d27a",
    name: "골든 스니치 · Snitch",
    tag: "이 게임의 신",
    body: "호두 크기 황금 구체 안에 회피 챔피언 AI. 추격자의 미래 위치를 예측해 반대로 도망. 손이 N밀리초 이상 감싸야 포획 성립.",
    quip: "\u201c드론 레이싱 회피 AI를 호두에 욱여넣었다.\u201d",
  },
];

const layers = [
  {
    no: "01",
    title: "중앙 집중 회피 — \u201c디멘터\u201d",
    body: "모든 기체가 RTK-GPS와 UWB로 자기 위치를 cm 단위로 중앙 서버에 보고. 초당 수백 번 충돌을 예측하고, 위험 페어가 잡히면 0.05초 만에 한 쪽에 회피를 명령합니다.",
  },
  {
    no: "02",
    title: "기체 자율 회피 — 엣지 자율성",
    body: "중앙 서버가 죽거나 통신이 끊겨도, 각 기체가 자체 라이다로 알아서 피합니다. \u201c공은 사람을 절대 들이받지 않는다\u201d는 불변 규칙은 펌웨어에 하드코딩 — 수정 불가.",
  },
  {
    no: "03",
    title: "물리적 안전 — 재질",
    body: "그래도 닿으면: 전부 에어백·폼·덕티드 팬. 노출 프로펠러 0개. 선수는 헬멧·고글·5점식 하네스 풀착용. 경기장엔 항공모함 착함 그물 스타일 안전망.",
  },
];

const phases = [
  { ph: "Phase 0", now: true, title: "종이 위", body: "기획서·룰북·안전 컨셉. 하드웨어 0, 코드 0. 당신은 지금 여기.", badge: "NOW" },
  { ph: "Phase 1", title: "공만 먼저", body: "사람 빼고 공 3종 군집드론부터. 빈 체육관. 죽을 일 없음." },
  { ph: "Phase 2", title: "무인 빗자루", body: "모래주머니 더미 태우고 지오펜스·자동호버·추락안전 검증. 더미는 안 운다." },
  { ph: "Phase 3", title: "유인 단독비행", body: "안전요원 1명, 저고도, 그물 위. \u201c사람이 진짜 날았다\u201d 최초 영상." },
  { ph: "Phase 4", title: "1 vs 1", body: "선수 2명 + 공 1개 미니 매치. 충돌회피 실전 검증." },
  { ph: "Phase 5", title: "풀 매치", body: "7 vs 7 + 공 3종. 초청 관중. 역사적 개막전." },
];

export default function App() {
  return (
    <main>
      <Hero />

      {/* MANIFESTO */}
      <section className="section manifesto" id="manifesto">
        <Reveal>
          <div className="eyebrow">왜 아무도 안 했는가</div>
          <p className="pull">
            인류 스포츠의 한계는 <b>2차원</b>이었습니다. 우리는 X축·Y축에 갇혀
            있었죠. <b>Z축이 비어 있었습니다.</b> 하늘이 비어 있었습니다.
          </p>
        </Reveal>
        <Reveal>
          <p className="lead">
            할 수 있는 놈은 돈이 없었고, 돈 있는 놈은 해리포터를 안 봤습니다.
            그런데 보세요 — <b>eVTOL</b>은 이미 유인 테스트 수천 회,{" "}
            <b>드론 군집</b>은 올림픽 개막식 하늘에 2000대,{" "}
            <b>라이다</b>는 택배 박스값이 됐습니다. 부품이 다 매대에 깔려 있어요.
            우리는 이걸 <b>존나 멍청한 방식으로 조립</b>할 뿐입니다. 그게
            혁신입니다.
          </p>
        </Reveal>
      </section>

      {/* BALLS */}
      <section className="section" id="balls">
        <Reveal>
          <div className="eyebrow">핵심 발명품</div>
          <h2 className="h2">
            인사이드아웃 <em>드론볼</em>
          </h2>
          <p className="lead">
            지금까지는 드론에 공 껍데기를 <b>씌웠습니다.</b> 그럼 프로펠러
            바람이 막혀 안 뜨죠. 우리는 발상을 뒤집습니다 — 바깥은 푹신한
            에어백 쉘, 안쪽엔 뒤지게 작은 군집 드론. <b>안에서 밖을 봅니다.</b>{" "}
            관중은 그냥 공이 의지를 갖고 날아다닌다고 느끼죠. 그게 마법입니다.
            마법은 숨겨진 엔지니어링의 다른 이름입니다.
          </p>
        </Reveal>
        <div className="grid3">
          {balls.map((b, i) => (
            <Reveal key={b.name} className="card" style={{ transitionDelay: `${i * 90}ms` }}>
              <div className="card__dot" style={{ background: b.color, color: b.color }} />
              <h3>{b.name}</h3>
              <span className="tag">{b.tag}</span>
              <p>{b.body}</p>
              <p className="quip">{b.quip}</p>
            </Reveal>
          ))}
        </div>
      </section>

      {/* SAFETY */}
      <section className="section" id="safety">
        <Reveal>
          <div className="eyebrow">3중 안전망 — 이게 생사를 가른다</div>
          <h2 className="h2">
            안 죽는다. <em>두 개가 고장나도.</em>
          </h2>
          <p className="lead">
            스포츠인데 14명이 드론 타고 공중에서 몸싸움하고 공 3개가
            자율비행합니다. 이거 안 부딪히게 하는 게 프로젝트의 80%예요.
            나머지 20%가 “멋있게”.
          </p>
        </Reveal>
        <div className="layers">
          {layers.map((l, i) => (
            <Reveal key={l.no} className="layer" style={{ transitionDelay: `${i * 80}ms` }}>
              <div className="layer__no">{l.no}</div>
              <div>
                <h4>{l.title}</h4>
                <p>{l.body}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* ROADMAP */}
      <section className="section" id="roadmap">
        <Reveal>
          <div className="eyebrow">로드맵 — 단계별로 안 죽으면서</div>
          <h2 className="h2">
            2030, <em>RQL 개막전.</em>
          </h2>
          <p className="lead">
            관중석에서 누군가 웁니다. 그게 J.K. 롤링이든 아니든 상관없어요.
            우린 날았으니까.
          </p>
        </Reveal>
        <div className="road">
          {phases.map((p, i) => (
            <Reveal
              key={p.ph}
              className={`phase ${p.now ? "now" : ""}`}
              style={{ transitionDelay: `${i * 60}ms` }}
            >
              {p.badge && <span className="badge">{p.badge}</span>}
              <span className="ph">{p.ph}</span>
              <h5>{p.title}</h5>
              <p>{p.body}</p>
            </Reveal>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="section cta">
        <Reveal>
          <h2 className="h2">
            가자. 인류 최초로 <em>진짜 빗자루</em>를 띄우자.
          </h2>
          <div className="row">
            <a className="btn" href="#manifesto">
              투자 데크 받기
            </a>
            <a
              className="btn btn--ghost"
              href="https://github.com/gkjuwon-tech/Quidditch"
              target="_blank"
              rel="noreferrer"
            >
              기획서 전문 읽기
            </a>
          </div>
          <p className="hero__note" style={{ marginTop: 28 }}>
            “마법 아니에요. 그냥 우리가 충돌회피 알고리즘을 존나 잘 짰을 뿐이에요.”
          </p>
        </Reveal>
      </section>

      <footer className="footer">
        <div>
          NIMBUS-9¾ · 퀴디치를 현실로 — Phase 0, 종이 위
        </div>
        <div className="footer__links">
          <span className="soon" style={{ opacity: 0.5 }}>코덱스 (준비중)</span>
          <span className="soon" style={{ opacity: 0.5 }}>엔지니어링 (준비중)</span>
          <span className="soon" style={{ opacity: 0.5 }}>후원 (준비중)</span>
          <a href="https://github.com/gkjuwon-tech/Quidditch" target="_blank" rel="noreferrer">
            GitHub ↗
          </a>
        </div>
      </footer>
    </main>
  );
}
