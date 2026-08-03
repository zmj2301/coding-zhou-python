// VaseKiller4
oS.Init(
	{
		PName: [oCherryBomb, oSeedRepeater2, oSeedWallNut, oSeedPotatoMine, oSeedSnowPea, oSeedPeashooter, oSeedSquash, oSeedThreepeater, oSeedPlantern],
		ZName: [oZombie, oZombie2, oZombie3, oJackinTheBoxZombie, oBucketheadZombie, oCXZombie],
		PicArr: ["images/interface/background2.jpg", "images/interface/trophy.png", "images/interface/PointerDown.gif", "images/interface/Stripe.png"],
		backgroundImage: "images/interface/background2.jpg",
		DKind: 0,
		ShowScroll: false,
		ProduceSun: false,
		LevelName: "Ace of Vase",
		LvlEName: "vasebreaker9",
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
			ZombieP: [0, 0, 0, 0, 0, 0, 0, 0, 3, 4, 4, 4, 4, 4, 5],
			PlantP: [1, 1, 1, 1, 1, 1, 2, 3, 4, 4, 5, 5, 6, 6, 6, 6, 6, 7, 7, 8],
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
