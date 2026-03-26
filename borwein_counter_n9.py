from manim import *
import numpy as np
import itertools
import math
from fractions import Fraction

class BorweinCounterN9_Infinity(MovingCameraScene):
    def construct(self):
        # ==========================================
        # ★ 設定 (N=9まで拡張版、-\infty to \infty)
        # ==========================================
        N_MAX = 9        
        DX = 0.002       
        X_RANGE = 5.0    
        
        SCAN_TIME = 4.0  
        RELAY_TIME = 2.0 
        WAIT_TIME = 0.5  
        # ==========================================

        # --- ★ 追加：Borwein積分の厳密な有理数値を計算する関数 ---
        # 積分公式に基づき、fractionsモジュールを使って誤差ゼロの厳密計算を行う
        def get_borwein_exact_fraction(N_val):
            a = [Fraction(1, 2*k + 1) for k in range(N_val)]
            M = len(a)
            n = M - 1

            sum_val = Fraction(0)
            for gamma in itertools.product([1, -1], repeat=M):
                prod_gamma = 1
                b_gamma = Fraction(0)
                for g, val in zip(gamma, a):
                    prod_gamma *= g
                    b_gamma += g * val
                
                sgn = 1 if b_gamma > 0 else (-1 if b_gamma < 0 else 0)
                sum_val += prod_gamma * (b_gamma ** n) * sgn

            prod_a = Fraction(1)
            for val in a:
                prod_a *= val

            # \int_{-\infty}^\infty 向けの係数 (2^{n+1} で割る)
            multiplier = Fraction(1, (2**(n+1)) * math.factorial(n) * prod_a)
            return multiplier * sum_val

        # アニメーション前に各Nの厳密なTeX文字列を自動計算してストックしておく
        exact_tex_strings = {}
        for n_val in range(1, N_MAX + 1):
            frac = get_borwein_exact_fraction(n_val)
            diff = Fraction(1) - frac
            if diff == 0:
                exact_tex_strings[n_val] = r"= \pi"
            else:
                # N=8以降で発生する「欠け」を有理数のまま文字列化
                exact_tex_strings[n_val] = rf"= \pi - \frac{{{diff.numerator}}}{{{diff.denominator}}} \pi"
        # ---------------------------------------------------------

        self.camera.background_color = BLACK
        self.camera.frame.scale(1.2).shift(DOWN * 0.2)

        # -----------------------
        # 1. データ事前生成 (-\infty to \infty)
        # -----------------------
        xs = np.arange(-X_RANGE, X_RANGE + DX, DX)
        center_idx = len(xs) // 2
        
        graph_data = []
        center_values = []
        
        # N=1 (Rect)
        ys = np.zeros_like(xs)
        mask = (xs >= -1) & (xs <= 1)
        ys[mask] = 1.0
        graph_data.append(ys.copy())
        center_values.append(ys[center_idx])
        
        # N=2 ～ N_MAX
        current_ys = ys.copy()
        for k in range(1, N_MAX):
            denom = 2*k + 1
            a = 1.0 / denom
            w_pixels = int(np.round(2 * a / DX))
            if w_pixels < 1: w_pixels = 1
            kernel = np.ones(w_pixels) / (w_pixels * DX)
            
            current_ys = np.convolve(current_ys, kernel, mode='same') * DX
            graph_data.append(current_ys.copy())
            center_values.append(current_ys[center_idx])

        # -----------------------
        # 2. 描画セットアップ
        # -----------------------
        axes_config = {"stroke_color": LIGHT_GREY, "stroke_width": 2}
        
        axes_top = Axes(x_range=[-4, 4, 1], y_range=[0, 1.3, 1], x_length=9, y_length=2.5, 
                        tips=False, axis_config=axes_config)
        axes_bot = Axes(x_range=[-4, 4, 1], y_range=[0, 1.3, 1], x_length=9, y_length=2.5, 
                        tips=False, axis_config=axes_config)

        layout = VGroup(axes_top, axes_bot).arrange(DOWN, buff=2.2)
        layout.to_edge(UP, buff=0.8)
        self.add(layout)
        
        self.add(MathTex(r"\text{Input}").next_to(axes_top, UP+LEFT).set_color(BLUE))
        self.add(MathTex(r"\text{Output}").next_to(axes_bot, UP+LEFT).set_color(YELLOW))

        def get_poly(ax, y_data, color, opacity=1.0):
            pts = [ax.c2p(x, y) for x, y in zip(xs[::10], y_data[::10]) if abs(x) < 4.2]
            if not pts: return VMobject()
            pts_closed = [ax.c2p(pts[0][0], 0)] + pts + [ax.c2p(pts[-1][0], 0)]
            poly = VMobject().set_points_as_corners(pts_closed)
            poly.set_stroke(color, 3)
            poly.set_fill(color, opacity=0.2 if opacity < 1 else 0)
            return poly

        top_graph = get_poly(axes_top, graph_data[0], color=BLUE)
        self.add(top_graph)
        
        # --- 情報パネル ---
        n_tracker = ValueTracker(1)
        ans_tracker = ValueTracker(center_values[0])

        info_panel = always_redraw(lambda: VGroup(
             VGroup(
                 MathTex("N = ").set_color(WHITE),
                 DecimalNumber(n_tracker.get_value(), num_decimal_places=0).set_color(YELLOW)
             ).arrange(RIGHT),
             VGroup(
                 MathTex(r"\text{Answer} \approx ").set_color(WHITE),
                 DecimalNumber(ans_tracker.get_value() * np.pi, num_decimal_places=12).set_color(GREEN)
             ).arrange(RIGHT),
             VGroup(
                 MathTex(r"\approx ").set_color(WHITE),
                 DecimalNumber(ans_tracker.get_value(), num_decimal_places=12).set_color(GREEN),
                 MathTex(r"\pi").set_color(GREEN)
             ).arrange(RIGHT)
        ).arrange(DOWN, aligned_edge=LEFT).scale(1.1).to_corner(UR, buff=0.8))
        
        self.add(info_panel)

        def get_integrand_tex(n_val):
            n = int(round(n_val)) 
            terms = []
            for k in range(n):
                denom = 2 * k + 1
                if denom == 1:
                    terms.append(r"\frac{\sin(x)}{x}")
                else:
                    terms.append(rf"\frac{{\sin(x/{denom})}}{{x/{denom}}}")
            return r"\int_{-\infty}^\infty " + "".join(terms) + r" \, dx"

        def get_exact_value_tex(n_val):
            n = int(round(n_val))
            # 自動計算しておいた辞書から、そのNに対応する厳密な有理数文字列を引っ張ってくる
            return exact_tex_strings.get(n, r"= \pi")

        integral_panel = always_redraw(lambda: VGroup(
            MathTex(get_integrand_tex(n_tracker.get_value())),
            MathTex(get_exact_value_tex(n_tracker.get_value())).set_color(GREEN)
        ).arrange(RIGHT).scale(0.5).move_to(layout.get_center()))
        
        self.add(integral_panel)
        self.wait(WAIT_TIME)

        # -----------------------
        # 3. アニメーションループ
        # -----------------------
        for i in range(N_MAX - 1):
            next_N = i + 2
            denom = 2*(i+1) + 1
            a_win = 1.0 / denom
            target_ans = center_values[i+1]

            if next_N == 8:
                alert_text = Text("Theoretical Breakpoint!", color=RED).scale(0.8).to_edge(RIGHT).shift(DOWN * 1.0)
                self.play(FadeIn(alert_text, run_time=0.5))
                self.wait(1.0)
                self.play(FadeOut(alert_text, run_time=0.5))

            window_text = MathTex(r"\text{Window Width: } \frac{2}{" + str(denom) + "}").scale(0.9).set_color(BLUE_D)
            window_text.move_to(layout.get_center()).shift(UP * 0.7)
            self.play(Write(window_text), run_time=1.0)
            self.wait(0.5)

            scan_tracker = ValueTracker(-4.2)
            
            moving_window = always_redraw(lambda: Polygon(
                axes_top.c2p(scan_tracker.get_value() - a_win, 0),
                axes_top.c2p(scan_tracker.get_value() - a_win, 1.2),
                axes_top.c2p(scan_tracker.get_value() + a_win, 1.2),
                axes_top.c2p(scan_tracker.get_value() + a_win, 0),
            ).set_stroke(BLUE, 3).set_fill(opacity=0))
            
            def get_shaded_area():
                xc = scan_tracker.get_value()
                idx_s = int((xc - a_win - xs[0])/DX)
                idx_e = int((xc + a_win - xs[0])/DX)
                idx_s = max(0, idx_s); idx_e = min(len(xs)-1, idx_e)
                if idx_s >= idx_e: return VGroup()
                
                current_y_data = graph_data[i]
                pts = [axes_top.c2p(xs[idx_s], 0)]
                pts += [axes_top.c2p(x, y) for x, y in zip(xs[idx_s:idx_e:20], current_y_data[idx_s:idx_e:20])]
                pts += [axes_top.c2p(xs[idx_e], 0)]
                return Polygon(*pts).set_stroke(width=0).set_fill(RED, opacity=0.5)

            moving_shade = always_redraw(get_shaded_area)
            bot_graph_full = get_poly(axes_bot, graph_data[i+1], color=YELLOW, opacity=0.3)
            
            self.add(moving_window, moving_shade)
            self.play(
                scan_tracker.animate.set_value(4.2),
                Create(bot_graph_full),
                run_time=SCAN_TIME,
                rate_func=linear
            )
            self.remove(moving_window, moving_shade)
            
            target_top_graph = get_poly(axes_top, graph_data[i+1], color=BLUE)
            
            self.play(
                FadeOut(top_graph, run_time=RELAY_TIME*0.5),
                FadeOut(window_text, run_time=RELAY_TIME*0.5),
                ReplacementTransform(bot_graph_full, target_top_graph, run_time=RELAY_TIME),
                n_tracker.animate.set_value(next_N),
                ans_tracker.animate.set_value(target_ans), 
            )
            
            top_graph = target_top_graph
            self.wait(WAIT_TIME)

        final_msg = Text("Still visually flat at N=9", font_size=36).set_color(YELLOW).move_to(layout.get_center()).shift(UP * 0.7)
        self.play(Write(final_msg))
        self.wait(3)

# ファイル名は borwein_counter_n9.py

# cd "C:\Dev\manim"
# .\.venv\Scripts\activate
# manim -pql "C:\Users\takas\OneDrive\math workspace\borwein_counter_n9.py" BorweinCounterN9_Infinity --media_dir "C:\Dev\manim\media"
# manim -pqh "C:\Users\takas\OneDrive\math workspace\borwein_counter_n9.py" BorweinCounterN9_Infinity --media_dir "C:\Dev\manim\media"
