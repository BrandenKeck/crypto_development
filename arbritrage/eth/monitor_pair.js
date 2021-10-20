// Imports
const { ChainId, Fetcher } = require ('@uniswap/sdk');
const ethers = require("ethers");
const keys = require('./keys.json');
const tokens = require('./tokens.json');
const chainId = ChainId.MAINNET;

// Connection to Ether Node
// Currently using an Infura API key in an untracked file
const customHttpProvider = new ethers.providers.JsonRpcProvider(keys['infura_node']);

// this ABI object works for both Uniswap and SushiSwap
const uniswapAbi = ["event Swap(address indexed sender, uint amount0In, uint amount1In, uint amount0Out, uint amount1Out, address indexed to)"];

// Get swap amounts from a real network transaction
// Imported Directly: https://gist.github.com/jotto/81ef912e3db07b60ac643b778714c38f
function getAmountsFromSwapArgs(swapArgs) {

  const { amount0In, amount0Out, amount1In, amount1Out } = swapArgs;

  let token0AmountBigDecimal = amount0In;
  if (token0AmountBigDecimal.eq(0)) {token0AmountBigDecimal = amount0Out;}

  let token1AmountBigDecimal = amount1In;
  if (token1AmountBigDecimal.eq(0)) {token1AmountBigDecimal = amount1Out;}

  return { token0AmountBigDecimal, token1AmountBigDecimal };
}

// Extract price based on swap amounts
// Imported Directly: https://gist.github.com/jotto/81ef912e3db07b60ac643b778714c38f
function convertSwapEventToPrice({ swapArgs, token0Decimals, token1Decimals }) {

  const {token0AmountBigDecimal, token1AmountBigDecimal} = getAmountsFromSwapArgs(swapArgs);
  console.log("TK1: " + token0AmountBigDecimal);
  console.log("TK2: " + token1AmountBigDecimal);

  const token0AmountFloat = parseFloat(ethers.utils.formatUnits(token0AmountBigDecimal, token0Decimals));
  const token1AmounFloat = parseFloat(ethers.utils.formatUnits(token1AmountBigDecimal, token1Decimals));
  console.log("TK1: " + token0AmountFloat);
  console.log("TK2: " + token1AmounFloat);

  if (token1AmounFloat > 0) {
    const priceOfToken0InTermsOfToken1 = token0AmountFloat / token1AmounFloat;
    return { price: priceOfToken0InTermsOfToken1, volume: token0AmountFloat };
  }

  return null;
}

// Monitor swap price based on actual transactions
// Modified From: https://gist.github.com/jotto/81ef912e3db07b60ac643b778714c38f
const monitor_pair = async (sym0, sym1) => {

  // Get Token Pair Hash Address
  const token0 = await Fetcher.fetchTokenData(chainId, tokens[sym0], customHttpProvider);
	const token1 = await Fetcher.fetchTokenData(chainId, tokens[sym1], customHttpProvider);
	const pair = await Fetcher.fetchPairData(token0, token1, customHttpProvider);
  const uniswapExchange = pair.liquidityToken.address
  console.log("POOL: " + uniswapExchange);

  // Extract swap contracts
  const uniswapContract = new ethers.Contract(
    uniswapExchange,
    uniswapAbi,
    customHttpProvider
  );
  const filter = uniswapContract.filters.Swap();

  // Analyze contract and return swap price
  uniswapContract.on(filter, (from, a0in, a0out, a1in, a1out, to, event) => {
    console.log("FROM: " + from);
    console.log("TO: " + to);
    console.log("TK1: " + a0in);
    console.log("TK1: " + a0out);
    console.log("TK2: " + a1in);
    console.log("TK2: " + a1out);

    const { price, volume } = convertSwapEventToPrice({
      swapArgs: event.args,
      token0Decimals: token0.decimals,
      token1Decimals: token1.decimals,
    });
    console.log({ price, volume });
  });

}

// Run the program if args provided
if(process.argv[2] != undefined && process.argv[3] != undefined){
	if(Object.prototype.hasOwnProperty.call(tokens, process.argv[2]) && Object.prototype.hasOwnProperty.call(tokens, process.argv[3])){
		monitor_pair(process.argv[2], process.argv[3]);
	}else{
		console.log("ERROR: ONE OR BOTH ERC20 TOKENS NOT FOUND")
	}
}else{
	console.log("ERROR: ONE OR BOTH ARGS ARE UNDEFINED")
}
