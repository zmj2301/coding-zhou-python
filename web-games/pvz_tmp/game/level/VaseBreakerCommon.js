// VaseBreakerCommon.js - 罐子关卡公共逻辑
// 提取 vasebreaker1~9 中的重复代码，遵循 DRY 原则

/**
 * 标准罐子生成逻辑
 * @param {Object} vaseConfig - 罐子配置对象，包含 Left, Right, GreenNum, ZombieP, PlantP, SunP
 */
function standardVaseRiddleAutoGrow(vaseConfig) {
	var P = vaseConfig;
	var L = P.Left;
	var R = P.Right;
	var GNum = P.GreenNum;
	var VaseList = [];
	var GroundList = [];

	// 生成罐子列表
	for (var O in P.ZombieP) {
		VaseList.push({
			Type: "Zombie",
			Value: oS.ZName[P.ZombieP[O]],
		});
	}
	for (var O in P.PlantP) {
		VaseList.push({ Type: "Plants", Value: oS.PName[P.PlantP[O]] });
	}
	for (var O in P.SunP) {
		VaseList.push({ Type: "SunNum", Value: P.SunP[O] });
	}

	// 生成格子列表
	for (; L <= R; ++L) {
		for (var Q = 1; Q <= oS.R; ++Q) {
			GroundList.push([Q, L]);
		}
	}

	// 打乱两者
	VaseList.sort(() => {
		return Math.random() - 0.5;
	});
	GroundList.sort(() => {
		return Math.random() - 0.5;
	});

	// 生成罐子
	while (VaseList.length && GroundList.length) {
		var Top = VaseList.at(-1);
		var Pos = GroundList.at(-1);

		oFlowerVase.prototype.SpecialBirth(Pos[0], Pos[1], Top.Type === "Plants" ? GNum-- > 0 : 0, Top); // 生成罐子

		(--VaseList.length, --GroundList.length);
	}
}

/**
 * 标准罐子关卡启动逻辑
 */
function standardVaseStartGame() {
	(oP.Monitor(), SetVisible($("tdShovel"), $("dFlagMeter"), $("dTop")));
	(StopMusic(), PlayMusic((oS.LoadMusic = oS.StartGameMusic)));
	for (var i in ArCard) {
		DoCoolTimer(i, 0);
	}
	var f = function () {
		// 检测这一部分是否结束
		if (oFlowerVase.prototype.GetLevelStatus()) {
			oP.FlagToEnd();
		} else {
			oSym.addTask(100, f, []);
		}
	};

	(oS.RiddleAutoGrow(), f()); // f 的调用一定要在生成罐子后面
}
