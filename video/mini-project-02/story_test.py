"""20-second test of the new storyboard opening (Act 0). Run:
    manimgx render story_test.py OpeningTest
"""

import manimgx as m

m.config.background_color = "#0A1020"
INK, MUTED, GOLD = "#EAF0F7", "#8DA2BA", "#F5B841"
B = 0.625  # one beat at 96 BPM; every timing below is in beats


def beats(n: float) -> float:
    return n * B


class OpeningTest(m.Scene):
    def construct(self) -> None:
        # 0.1 — title (4 bars)
        title = m.Text("Where the Memory Goes", font_size=60, color=INK)
        self.play(m.Write(title), run_time=beats(8))
        self.play(title.animate.scale(0.6).to_edge(m.UP, buff=0.5), run_time=beats(4))
        self.wait(beats(4))

        # 0.2 — reserved pages, one per beat (4 bars)
        pages = m.VGroup(*[
            m.Square(0.9, color=MUTED, stroke_width=2, fill_color=GOLD, fill_opacity=0) for _ in range(8)
        ]).arrange(m.RIGHT, buff=0.3).move_to([0, 0.3, 0])
        line1 = m.Text("A program asks for memory. The computer says yes,", font_size=28, color=INK)
        line2 = m.Text("but hands it over only when it is used.", font_size=28, color=INK)
        words = m.VGroup(line1, line2).arrange(m.DOWN, buff=0.15).move_to([0, -2.6, 0])
        self.play(m.LaggedStart(*[m.Create(p) for p in pages], lag_ratio=1), m.Write(words), run_time=beats(8))
        self.wait(beats(8))

        # 0.3 — the first touch is a fault (4 bars)
        token = m.Square(0.22, fill_color=GOLD, fill_opacity=1, stroke_width=0).move_to([-6.5, 2.0, 0])
        trail = m.TracedPath(token.get_center, stroke_color=GOLD, stroke_width=3, dissipating_time=0.6)
        self.add(trail, token)
        new_words = m.VGroup(
            m.Text("The first touch pauses the program.", font_size=28, color=INK),
            m.Text("That pause is a page fault.", font_size=28, color=GOLD),
        ).arrange(m.DOWN, buff=0.15).move_to(words)
        self.play(token.animate.move_to(pages[0].get_center()), m.Unwrite(words), run_time=beats(4))
        dim = m.Rectangle(width=14.2, height=8, stroke_width=0, fill_color="#000000", fill_opacity=0.5)
        self.play(m.FadeIn(dim), run_time=beats(1))  # the pause
        self.play(
            m.FadeOut(dim), m.Flash(pages[0], color=GOLD),
            pages[0].animate.set_fill(GOLD, opacity=0.9), m.FadeOut(token),
            m.Write(new_words), run_time=beats(3),
        )
        self.play(
            m.LaggedStart(*[p.animate.set_fill(GOLD, opacity=0.9) for p in pages[1:]], lag_ratio=1),
            run_time=beats(7),
        )
        self.wait(beats(1))
