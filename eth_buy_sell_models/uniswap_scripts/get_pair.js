// Imports
const { ChainId, Fetcher, WETH, Route, Trade, TokenAmount, TradeType } = require ('@uniswap/sdk');
const ethers = require('ethers');
const keys = require('./keys.json');
const tokens = require('./tokens.json');
const chainId = ChainId.MAINNET;

// Connection to Ether Node
// Currently using an Infura API key in an untracked file
const customHttpProvider = new ethers.providers.JsonRpcProvider(keys['infura_node']);

// Node Get Pair Information Test
const get_pair = async (sym1, sym2) => {

	// One way of getting tokens and their trade information
	const token1 = await Fetcher.fetchTokenData(chainId, tokens[sym1], customHttpProvider);
	const token2 = await Fetcher.fetchTokenData(chainId, tokens[sym2], customHttpProvider);
	const pair = await Fetcher.fetchPairData(token1, token2, customHttpProvider);
	const route = new Route([pair], token2);
	const trade = new Trade(route, new TokenAmount(token2, '1000000000000000'), TradeType.EXACT_INPUT);

	// Output relevant information
	console.log("Mid Price " + sym1 + " --> " + sym2 + ":", route.midPrice.toSignificant(8));
	console.log("Mid Price " + sym2 + " --> " + sym1 + ":", route.midPrice.invert().toSignificant(8));
	console.log("Mid Price (After Trade) " + sym1 + " --> " + sym2 + ":", trade.nextMidPrice.toSignificant(8));
	console.log("Execution Price " + sym1 + " --> " + sym2 + ":", trade.executionPrice.toSignificant(8));
	console.log("Pair Address: " + pair.liquidityToken.address);

}

// Run the program if args provided
if(process.argv[2] != undefined && process.argv[3] != undefined){
	if(Object.prototype.hasOwnProperty.call(tokens, process.argv[2]) && Object.prototype.hasOwnProperty.call(tokens, process.argv[3])){
		get_pair(process.argv[2], process.argv[3]);
	}else{
		console.log("ERROR: ONE OR BOTH ERC20 TOKENS NOT FOUND")
	}
}else{
	console.log("ERROR: ONE OR BOTH ARGS ARE UNDEFINED")
}
