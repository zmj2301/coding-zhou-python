package com.workbuddy.xiangtanbus;

import android.app.Activity;
import android.app.AlertDialog;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.TextUtils;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import java.util.List;

/** 湘潭实时公交 —— 主界面。 */
public class MainActivity extends Activity {

    private static final int BG = 0xFFF5F7FA;
    private static final int CARD = 0xFFFFFFFF;
    private static final int PRIMARY = 0xFF1B73E8;
    private static final int SUCCESS = 0xFF22A06B;
    private static final int WARN = 0xFFEB9E0D;
    private static final int TEXT = 0xFF21272F;
    private static final int SUBTLE = 0xFF6B7280;

    private EditText originInput, destInput;
    private Button searchBtn;
    private TextView statusView;
    private ProgressBar progress;
    private LinearLayout resultBox;
    private LinearLayout scrollContent;
    private LinearLayout rootView;

    private final Handler main = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(buildUi());
        // 调试开关：-e debugAuto 启动时自动执行一次查询（用于模拟器自动化验证）
        String auto = getIntent() != null ? getIntent().getStringExtra("debugAuto") : null;
        if (auto != null) {
            rootView.postDelayed(this::onSearch, 800);
        }
    }

    // ---------- UI 构建 ----------

    private int dp(float v) {
        return (int) TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v, getResources().getDisplayMetrics());
    }

    private LinearLayout buildUi() {
        LinearLayout root = new LinearLayout(this);
        rootView = root;
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(BG);
        root.setPadding(dp(16), dp(18), dp(16), dp(12));

        // 标题 + 版本号
        TextView title = new TextView(this);
        title.setText("🚌湘潭实时公交");
        title.setTextColor(TEXT);
        title.setTextSize(23);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        root.addView(title, lp(MATCH, WRAP, 0, 0, 0, 0));

        TextView ver = new TextView(this);
        ver.setText(String.format("版本 v%s · 构建%s · %s",
                ChelaileClient.APP_VERSION, BuildInfo.BUILD_NO, "湘潭"));
        ver.setTextColor(SUBTLE);
        ver.setTextSize(11);
        root.addView(ver, lp(MATCH, WRAP, 0, 2, 0, 0));

        // 输入卡片
        LinearLayout form = card();
        form.setPadding(dp(14), dp(14), dp(14), dp(14));
        ViewGroup.MarginLayoutParams fm = lp(MATCH, WRAP, 0, 14, 0, 0);

        form.addView(label("起点（支持小区 / 学校 / 地标）"), lp(MATCH, WRAP, 0, 0, 0, 0));
        originInput = input("未来素养");
        form.addView(originInput, lp(MATCH, dp(46), 0, 6, 0, 0));

        form.addView(label("终点（支持站名 / 地标）"), lp(MATCH, WRAP, 0, 10, 0, 0));
        destInput = input("翰林居");
        form.addView(destInput, lp(MATCH, dp(46), 0, 6, 0, 0));
        root.addView(form, fm);

        // 查询按钮
        searchBtn = new Button(this);
        searchBtn.setText("查询最优方案");
        searchBtn.setTextSize(16);
        searchBtn.setTextColor(Color.WHITE);
        searchBtn.setTypeface(Typeface.DEFAULT_BOLD);
        searchBtn.setAllCaps(false);
        searchBtn.setBackground(roundRect(PRIMARY, 10));
        searchBtn.setOnClickListener(v -> onSearch());
        root.addView(searchBtn, lp(MATCH, dp(52), 0, 0, 0, 0));

        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setMax(100);
        progress.setVisibility(View.GONE);
        LinearLayout.LayoutParams pp = lp(MATCH, dp(4), 0, 8, 0, 0);
        progress.setLayoutParams(pp);
        root.addView(progress);

        statusView = new TextView(this);
        statusView.setText("输入起终点，点「查询最优方案」");
        statusView.setTextColor(SUBTLE);
        statusView.setTextSize(13);
        root.addView(statusView, lp(MATCH, WRAP, 0, 6, 0, 0));

        // 结果区
        ScrollView sv = new ScrollView(this);
        sv.setFillViewport(true);
        scrollContent = new LinearLayout(this);
        scrollContent.setOrientation(LinearLayout.VERTICAL);
        sv.addView(scrollContent, new ScrollView.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        LinearLayout.LayoutParams sp = lp(MATCH, 0, 1, 10, 0, 0);
        sp.weight = 1f;
        sv.setLayoutParams(sp);
        root.addView(sv, sp);

        return root;
    }

    private TextView label(String text) {
        TextView t = new TextView(this);
        t.setText(text);
        t.setTextColor(SUBTLE);
        t.setTextSize(12);
        return t;
    }

    private EditText input(String hint) {
        EditText e = new EditText(this);
        e.setText(hint);
        e.setTextColor(TEXT);
        e.setTextSize(15);
        e.setSingleLine(true);
        e.setPadding(dp(12), 0, dp(12), 0);
        e.setBackground(roundRect(0xFFF0F3F7, 8));
        return e;
    }

    private LinearLayout card() {
        LinearLayout l = new LinearLayout(this);
        l.setOrientation(LinearLayout.VERTICAL);
        l.setBackground(roundRect(CARD, 12));
        return l;
    }

    private GradientDrawable roundRect(int color, int radius) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(color);
        g.setCornerRadius(dp(radius));
        return g;
    }

    /** 宽度占满父容器 */
    private static final int MATCH = LinearLayout.LayoutParams.MATCH_PARENT;
    /** 高度自适应 */
    private static final int WRAP = LinearLayout.LayoutParams.WRAP_CONTENT;

    private LinearLayout.LayoutParams lp(int w, int h, int top, int bottom, int l, int r) {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(w, h);
        p.setMargins(dp(l), dp(top), dp(r), dp(bottom));
        return p;
    }

    /** 宽度占满、高度自适应 */
    private LinearLayout.LayoutParams rowParams(int top, int bottom) {
        return lp(MATCH, WRAP, top, bottom, 0, 0);
    }

    // ---------- 查询 ----------

    private void onSearch() {
        final String o = originInput.getText().toString().trim();
        final String d = destInput.getText().toString().trim();
        if (o.isEmpty() || d.isEmpty()) {
            statusView.setText("请填写起点和终点");
            statusView.setTextColor(WARN);
            return;
        }

        setBusy(true);
        statusView.setTextColor(SUBTLE);
        statusView.setText("正在拉取实时车辆数据…");
        scrollContent.removeAllViews();
        startProgress();

        new Thread(() -> {
            try {
                final String[] od = new String[1], dd = new String[1];
                final List<Planner.Stop> origins = Planner.resolveOrigin(o, od);
                if (origins.isEmpty()) {
                    fail(od[0]); return;
                }
                final List<Planner.Stop> dests = Planner.resolveDestination(d, dd);
                if (dests.isEmpty()) {
                    fail("终点未找到：" + dd[0]); return;
                }
                final List<Planner.Plan> plans = Planner.plan(origins, dests, 6);
                final String desc = od[0] + "｜" + dd[0];
                main.post(() -> render(plans, desc));
            } catch (Exception ex) {
                fail("查询失败：" + ex.getMessage());
            }
        }).start();
    }

    private void startProgress() {
        progress.setVisibility(View.VISIBLE);
        progress.setProgress(0);
        main.post(new Runnable() {
            int p = 0;
            @Override public void run() {
                if (progress.getVisibility() != View.VISIBLE) return;
                p = (p + 7) % 100;
                progress.setProgress(p);
                main.postDelayed(this, 180);
            }
        });
    }

    private void setBusy(boolean busy) {
        searchBtn.setEnabled(!busy);
        searchBtn.setAlpha(busy ? 0.6f : 1f);
        searchBtn.setText(busy ? "查询中…" : "查询最优方案");
        if (!busy) progress.setVisibility(View.GONE);
    }

    private void fail(String msg) {
        main.post(() -> {
            setBusy(false);
            statusView.setText(msg);
            statusView.setTextColor(WARN);
            new AlertDialog.Builder(this)
                    .setTitle("提示").setMessage(msg)
                    .setPositiveButton("好", null).show();
        });
    }

    private void render(List<Planner.Plan> plans, String desc) {
        setBusy(false);
        statusView.setText(String.format("起点 %s　查询于 %s", desc,
                new java.text.SimpleDateFormat("HH:mm:ss").format(new java.util.Date())));
        statusView.setTextColor(SUCCESS);

        scrollContent.removeAllViews();
        if (plans.isEmpty()) {
            TextView t = new TextView(this);
            t.setText("未找到可行公交方案");
            t.setTextColor(WARN);
            t.setTextSize(14);
            scrollContent.addView(t, lp(MATCH, WRAP, 0, 0, 0, 0));
            return;
        }

        for (int i = 0; i < plans.size(); i++) {
            scrollContent.addView(planCard(i + 1, plans.get(i)),
                    lp(MATCH, WRAP, 0, 0, 0, 10));
        }
        Toast.makeText(this, "共 " + plans.size() + " 个方案", Toast.LENGTH_SHORT).show();
    }

    private View planCard(int index, Planner.Plan plan) {
        LinearLayout card = card();
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(14), dp(10), dp(14), dp(12));

        // 左侧色条
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);

        View bar = new View(this);
        bar.setBackground(roundRect(plan.hasRealtime ? SUCCESS : WARN, 2));
        row.addView(bar, new LinearLayout.LayoutParams(dp(4), dp(34)));

        TextView title = new TextView(this);
        title.setText(String.format("方案 %d  ·  总计 %.0f 分钟", index, plan.total));
        title.setTextColor(TEXT);
        title.setTextSize(16);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        LinearLayout.LayoutParams tp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1);
        tp.leftMargin = dp(10);
        row.addView(title, tp);

        TextView badge = new TextView(this);
        badge.setText("换乘 " + plan.transfers + " 次  ·  " + (plan.hasRealtime ? "实时" : "估算"));
        badge.setTextColor(plan.hasRealtime ? SUCCESS : WARN);
        badge.setTextSize(12);
        badge.setGravity(Gravity.RIGHT);
        row.addView(badge);

        card.addView(row, lp(MATCH, WRAP, 0, 6, 0, 0));

        for (Planner.Leg leg : plan.legs) {
            card.addView(legRow(leg), lp(MATCH, dp(34), 0, 0, 0, 0));
        }

        if (!TextUtils.isEmpty(plan.note)) {
            TextView note = new TextView(this);
            note.setText("⚠ " + plan.note);
            note.setTextColor(WARN);
            note.setTextSize(11);
            card.addView(note, lp(MATCH, WRAP, 0, 4, 0, 0));
        }
        return card;
    }

    private View legRow(Planner.Leg leg) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);

        TextView mins = new TextView(this);
        mins.setText(Math.round(leg.minutes) + "分");
        mins.setTextColor("bus".equals(leg.kind) ? PRIMARY : SUCCESS);
        mins.setTextSize(15);
        mins.setTypeface(Typeface.DEFAULT_BOLD);
        mins.setGravity(Gravity.CENTER);
        row.addView(mins, new LinearLayout.LayoutParams(dp(56), ViewGroup.LayoutParams.WRAP_CONTENT));

        TextView title = new TextView(this);
        title.setText(leg.title);
        title.setTextColor(TEXT);
        title.setTextSize(14);
        title.setSingleLine(true);
        title.setEllipsize(TextUtils.TruncateAt.END);
        LinearLayout.LayoutParams tp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1);
        tp.leftMargin = dp(4);
        row.addView(title, tp);

        TextView detail = new TextView(this);
        detail.setText(leg.detail);
        detail.setTextColor(SUBTLE);
        detail.setTextSize(11);
        detail.setSingleLine(true);
        detail.setGravity(Gravity.RIGHT | Gravity.CENTER_VERTICAL);
        row.addView(detail, new LinearLayout.LayoutParams(dp(110), ViewGroup.LayoutParams.WRAP_CONTENT));

        return row;
    }

    /** 便于测试时反射调用 */
    public void debugPlan(String origin, String dest) {
        originInput.setText(origin);
        destInput.setText(dest);
        onSearch();
    }
}
