// VaseKiller5
oS.Init(
	{
		PName: [oCherryBomb, oSeedRepeater2, oSeedHypnoShroom, oSeedSnowPea, oSeedPumpkinHead, oSeedThreepeater, oSeedSquash],
		ZName: [oZombie, oZombie2, oBucketheadZombie, oFootballZombie, oJackinTheBoxZombie],
		PicArr: ["images/interface/background2.jpg", "images/interface/trophy.png", "images/interface/PointerDown.gif", "images/interface/Stripe.png"],
		backgroundImage: "images/interface/background2.jpg",
		DKind: 0,
		ShowScroll: false,
		ProduceSun: false,
		LevelName: "M is for Metal",
		LvlEName: "vasebreaker5",
		CanSelectCard: 0,
		StartGameMusic: "Cerebrawl",
		SunNum: 0,
		RiddleAutoGrow() {
			standardVaseRiddleAutoGrow(oS.VaseArP);
		},
		StartGame: standardVaseStartGame,

		VaseArP: {
			GreenNum: 2,
			Left: 3,
			Right: 9,
			ZombieP: [0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 4],

			PlantP: [1, 1, 1, 1, 1, 1, 2, 2, 3, 3, 4, 4, 4, 5, 5, 5, 6, 6, 6, 6],
			SunP: [],
		},
	},
	0,
	{
		AutoSelectCard() {
			// 只选择樱桃炸弹
			SelectCard(oCherryBomb.prototype.EName);
		},
	}
);
