// 스크롤 리빌 애니메이션: 화면에 들어오는 요소에 is-visible 클래스 부여
const revealTargets = document.querySelectorAll("[data-reveal]");

const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        revealObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.15 }
);

revealTargets.forEach((el) => revealObserver.observe(el));

// 네비게이션 바: 스크롤 시 배경 강조
const nav = document.getElementById("nav");
window.addEventListener("scroll", () => {
  if (window.scrollY > 8) {
    nav.style.borderBottomColor = "rgba(110, 139, 255, 0.25)";
  } else {
    nav.style.borderBottomColor = "";
  }
});
