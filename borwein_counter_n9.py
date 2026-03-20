from manim import *
import numpy as np

class BorweinCounterN9(MovingCameraScene):
    def construct(self):
        # ==========================================
        # ★ 設定 (N=9まで拡張版)
        # ==========================================
        N_MAX = 9        # N=9まで計算！ (N=8の壁を超える)
        DX = 0.002       # 解像度
        X_RANGE = 4.0    # 計算範囲 (Nが増えると広がるため拡大)
        
        # 時間設定 (秒) - 回数が多いので少しだけテンポアップ
        SCAN_TIME = 4.0  
        RELAY_TIME = 2.0 
        WAIT_TIME = 0.5  
        # ==========================================

        self.camera.background_color = BLACK
        self.camera.frame.scale(1.1)

        # -----------------------
        # 1. データ事前生成
        # -----------------------
        xs = np.arange(-X_RANGE, X_RANGE + DX, DX)
        center_idx = len(xs) // 2
        
        graph_data = []
        center_values = []
        
        # N=1
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
        # 2. 描画セットアップ (範囲拡大)
        # -----------------------
        axes_config = {"stroke_color": LIGHT_GREY, "stroke_width": 2}
        
        # 軸の範囲を [-3, 3] に拡大
        axes_top = Axes(x_range=[-3, 3, 1], y_range=[0, 1.3, 1], x_length=12, y_length=3.0, 
                        tips=False, axis_config=axes_config)
        axes_bot = Axes(x_range=[-3, 3, 1], y_range=[0, 1.3, 1], x_length=12, y_length=3.0, 
                        tips=False, axis_config=axes_config)

        layout = VGroup(axes_top, axes_bot).arrange(DOWN, buff=1.5)
        layout.to_edge(UP, buff=1.0)
        self.add(layout)
        
        # ラベル
        self.add(MathTex(r"\text{Input}").next_to(axes_top, UP+LEFT).set_color(BLUE))
        self.add(MathTex(r"\text{Output}").next_to(axes_bot, UP+LEFT).set_color(YELLOW))

        # ポリゴン作成関数
        def get_poly(ax, y_data, color, opacity=1.0):
            # 間引き (step=10)
            pts = [ax.c2p(x, y) for x, y in zip(xs[::10], y_data[::10]) if abs(x) < 3.2]
            if not pts: return VMobject()
            pts_closed = [ax.c2p(pts[0][0], 0)] + pts + [ax.c2p(pts[-1][0], 0)]
            poly = VMobject().set_points_as_corners(pts_closed)
            poly.set_stroke(color, 3)
            poly.set_fill(color, opacity=0.2 if opacity < 1 else 0)
            return poly

        # 初期グラフ (N=1)
        top_graph = get_poly(axes_top, graph_data[0], color=BLUE)
        self.add(top_graph)
        
        # --- 情報パネル ---
        n_tracker = ValueTracker(1)
        height_tracker = ValueTracker(center_values[0])

        info_panel = always_redraw(lambda: VGroup(
             VGroup(
                 MathTex("N = ").set_color(WHITE),
                 DecimalNumber(n_tracker.get_value(), num_decimal_places=0).set_color(YELLOW)
             ).arrange(RIGHT),
             VGroup(
                 MathTex(r"\text{Height} \approx ").set_color(WHITE),
                 DecimalNumber(height_tracker.get_value(), num_decimal_places=15).set_color(GREEN)
             ).arrange(RIGHT)
        ).arrange(DOWN, aligned_edge=LEFT).scale(1.2).to_corner(UR, buff=1.0))
        
        self.add(info_panel)
        self.wait(WAIT_TIME)

        # -----------------------
        # 3. アニメーションループ
        # -----------------------
        for i in range(N_MAX - 1):
            next_N = i + 2
            denom = 2*(i+1) + 1
            a_win = 1.0 / denom
            target_height = center_values[i+1]

            # N=8 になる瞬間に特別なメッセージを出す演出を入れても面白いかも
            if next_N == 8:
                alert_text = Text("Theoretical Breakpoint!", color=RED).scale(0.8).to_edge(RIGHT)
                self.play(FadeIn(alert_text, run_time=0.5))
                self.wait(1.0)
                self.play(FadeOut(alert_text, run_time=0.5))

            # --- Phase 1: 窓の準備 ---
            window_text = MathTex(rf"\text{{Window Width: }} \frac{{2}}{{ {denom} }}").scale(1.0).set_color(BLUE_D)
            window_text.move_to(layout.get_center())
            self.play(Write(window_text), run_time=1.0)
            self.wait(0.5)

            # --- Phase 2: スキャン ---
            scan_tracker = ValueTracker(-3.2) # 範囲拡大に合わせて開始位置変更
            
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
                scan_tracker.animate.set_value(3.2), # 終了位置変更
                Create(bot_graph_full),
                run_time=SCAN_TIME,
                rate_func=linear
            )
            self.remove(moving_window, moving_shade)
            
            # --- Phase 3: リレー ---
            target_top_graph = get_poly(axes_top, graph_data[i+1], color=BLUE)
            
            self.play(
                FadeOut(top_graph, run_time=RELAY_TIME*0.5),
                FadeOut(window_text, run_time=RELAY_TIME*0.5),
                ReplacementTransform(bot_graph_full, target_top_graph, run_time=RELAY_TIME),
                n_tracker.animate.set_value(next_N),
                height_tracker.animate.set_value(target_height),
            )
            
            top_graph = target_top_graph
            self.wait(WAIT_TIME)

        # 終了後
        final_msg = Text("Still visually flat at N=9").scale(0.8).set_color(YELLOW).next_to(top_graph, UP)
        self.play(Write(final_msg))
        self.wait(3)

# ファイル名は borwein_counter_n9.py
# 出力: manim -pql "C:\Users\takas\OneDrive\math workspace\borwein_counter_n9.py" BorweinCounterN9 --media_dir "C:\Dev\manim\media"
# 出力: manim -pqh "C:\Users\takas\OneDrive\math workspace\borwein_counter_n9.py" BorweinCounterN9 --media_dir "C:\Dev\manim\media"