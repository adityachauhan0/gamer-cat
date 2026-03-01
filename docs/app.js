(() => {
    const ambient = document.getElementById("ambient");
    const hero = document.getElementById("hero-card");
    const layers = Array.from(document.querySelectorAll("[data-depth]"));
    const canvas = document.getElementById("fx-canvas");
    const ctx = canvas.getContext("2d");

    const particles = [];
    const particleCount = 65;

    const resize = () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    };

    const random = (min, max) => Math.random() * (max - min) + min;

    const buildParticles = () => {
        particles.length = 0;
        for (let i = 0; i < particleCount; i += 1) {
            particles.push({
                x: random(0, canvas.width),
                y: random(0, canvas.height),
                r: random(1, 2.9),
                vx: random(-0.24, 0.24),
                vy: random(-0.2, 0.2),
                hue: Math.random() > 0.5 ? 192 : 318
            });
        }
    };

    const draw = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        particles.forEach((p) => {
            p.x += p.vx;
            p.y += p.vy;

            if (p.x < -8) p.x = canvas.width + 8;
            if (p.x > canvas.width + 8) p.x = -8;
            if (p.y < -8) p.y = canvas.height + 8;
            if (p.y > canvas.height + 8) p.y = -8;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = `hsla(${p.hue}, 95%, 72%, 0.65)`;
            ctx.shadowBlur = 14;
            ctx.shadowColor = `hsla(${p.hue}, 95%, 72%, 0.45)`;
            ctx.fill();
        });

        requestAnimationFrame(draw);
    };

    window.addEventListener("mousemove", (e) => {
        const x = (e.clientX / window.innerWidth - 0.5) * 2;
        const y = (e.clientY / window.innerHeight - 0.5) * 2;

        layers.forEach((layer) => {
            const depth = Number(layer.dataset.depth || 0);
            layer.style.transform = `translate(${x * depth * 46}px, ${y * depth * 40}px)`;
        });

        if (hero) {
            hero.style.transform = `translate(${x * -6}px, ${y * -4}px)`;
        }
        if (ambient) {
            ambient.style.transform = `translate(${x * -3}px, ${y * -2}px)`;
        }
    });

    window.addEventListener("resize", () => {
        resize();
        buildParticles();
    });

    resize();
    buildParticles();
    draw();
})();
