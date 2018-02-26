#include <set>
#include <fstream>
#include <iostream>
using namespace std;
/*
A = 14, 2 = 15, s(mall joker) = 16, b(ig joker) = 17
0：要不起
1：单 2：双 3：三 4：三带一 5：三带二
6：单顺 7：双顺 8：三顺 9：三带一顺 10：三带二顺
11：炸弹 12：四带二
gameset.txt 第一排确定以上12种规则 第二三排写电脑与你的牌
区分大小写 不计顺序 以0结尾 

目前没有找到更好的hash函数……
*/ 
struct dpHash//当一方要不起或者开局的时候，对场上双方牌型的记录 
{
	int player;//先行方 
	long long cardHash[2];//双方牌型的五进制状态压缩 
	inline friend bool operator <(dpHash x, dpHash y)
	{
		if (x.player != y.player) return x.player < y.player;
		else if (x.cardHash[0] != y.cardHash[0]) return x.cardHash[0] < y.cardHash[0];
		else return x.cardHash[1] < y.cardHash[1];
	}
};
set <dpHash> dp[2];//记忆化搜索 
int card[2][18], newCard[2][18];//当前的牌与电脑预备在本轮出完后留下的牌 
bool typeAllowed[13];//确定启用哪些规则 
const int leastSeries[6] = {0,5,3,2,2,2};//连续几张牌以上才算顺子 
bool flagSeries[2][4][18][16];
const long long five[18] = {0,0,0,1,5,25,125,625,3125,15625,78125,390625,1953125,9765625,
			48828125,244140625,1220703125,6103515625};
bool attachFinder(int depth, int cardType, int beg, int num, 
					int index, int rest);//存在递归互相调用，先声明 

inline bool isEmpty(int player)//判断一方的牌是否已打完 
{
	for (int i=3;i<=17;++i)
		if (card[player][i]) return false;
	return true;
}
inline bool hasSeries(int player, int cardNum, int beg, int num)
{//判断一方是否有某种从某张牌开始的顺子 
	if (!flagSeries[player][cardNum][beg][num]) return false;

	for (int i=0;i<num;++i)
		if (card[player][beg+i] < cardNum) return false;
	return true;
}
inline void subSeries(int player, int cardNum, int beg, int num)
{//打出顺子 
	for (int i=0;i<num;++i)
		card[player][beg+i] -= cardNum;
}
inline void addSeries(int player, int cardNum, int beg, int num)
{//还原顺子 
	for (int i=0;i<num;++i)
		card[player][beg+i] += cardNum;
}
inline void newCardRecord()//记录下电脑预备在本轮出完后留下的牌 
{
	for (int i=0;i<2;++i)
		for (int j=3;j<=17;++j)
			newCard[i][j] = card[i][j];
}
inline void numTocard(int num)//输出牌 
{
	if (num <= 10) cout << num << " ";
	else if (num == 11) cout << "J ";
	else if (num == 12) cout << "Q ";
	else if (num == 13) cout << "K ";
	else if (num == 14) cout << "A ";
	else if (num == 15) cout << "2 ";
	else if (num == 16) cout << "s ";
	else cout << "b ";
}
dpHash hashCalc(int player)//当前牌型hash化 
{
	dpHash temp;
	temp.player = player;
	for (int i=0;i<2;++i)
	{
		temp.cardHash[i] = 0;
		for (int j=3;j<=17;++j)
			for (int k=0;k<card[i][j];++k)
				temp.cardHash[i] += five[j];
	}
	return temp;
} 
inline bool hashRecord(dpHash dpHashNow, bool ans)//搜索结果的记录 
{
	dp[ans].insert(dpHashNow);
	return ans;
}
void gameset()//游戏开局的设置 
{
	cout << "Make sure you have written down your own setting in gameset.txt." << endl; 
	cout << "Determine the rules you adopt of the 12 in the 1st line." << endl;
	cout << "The 2nd line consists of the cards of computer,ending with 0." << endl;
	cout << "The 3rd line consists of the cards of player,ending with 0." << endl;
	cout << "Both are case sensitive.Here s is for small joker while b is for big one." << endl;
	cout << "Game starts!" << endl << endl;
	
	ifstream fin("gameset.txt");
	for (int i=1;i<13;++i)//读入规则 
		fin >> typeAllowed[i];
	for (int i=0;i<2;++i)//读入双方牌型，以0结束 
	{
		string temp;
		fin >> temp;
		while (temp[0] != '0')
		{
			if (temp[0] >= '3' && temp[0] <= '9') ++ card[i][temp[0]-'0'];
			else if (temp[0] == '1') ++ card[i][10];
			else if (temp[0] == 'J') ++ card[i][11];
			else if (temp[0] == 'Q') ++ card[i][12];
			else if (temp[0] == 'K') ++ card[i][13];
			else if (temp[0] == 'A') ++ card[i][14];
			else if (temp[0] == '2') ++ card[i][15];
			else if (temp[0] == 's') ++ card[i][16];
			else if (temp[0] == 'b') ++ card[i][17];
			fin >> temp;
		}
	}
	cout << "Com:";//输出双方牌型 
	for (int i=17;i>=3;--i)
		for (int j=0;j<card[0][i];++j)
			numTocard(i);
	cout << endl << "Ply:";
	for (int i=17;i>=3;--i)
		for (int j=0;j<card[1][i];++j)
			numTocard(i);
	cout << endl;
}
void com()//电脑出牌 
{
	cout << "Computer's move:";
	for (int i=17;i>=3;--i)
		for (int j=0;j<card[0][i]-newCard[0][i];++j)
			numTocard(i);
	cout << endl << "After computer's move:" << endl;
	cout << "Com:";
	for (int i=17;i>=3;--i)
	{
		card[0][i] = newCard[0][i];
		for (int j=0;j<card[0][i];++j)
			numTocard(i);
	}
	cout << endl << "Ply:";
	for (int i=17;i>=3;--i)
		for (int j=0;j<card[1][i];++j)
			numTocard(i);
	cout << endl;
}
void ply(int &cardType, int &beg, int &num)//人类出牌，在引用中记录下出牌信息 
{	
	if (isEmpty(0))
	{
		cout << "You lose!" << endl;
		system("pause");
		exit(0);
	}
	else
	{
		cout << "Your move(without cheching,end with 0):";
		//TODO
		
		string temp;
		cin >> temp;
		while (temp[0] != '0')
		{
			if (temp[0] >= '3' && temp[0] <= '9') -- card[1][temp[0]-'0'];
			else if (temp[0] == '1') -- card[1][10];
			else if (temp[0] == 'J') -- card[1][11];
			else if (temp[0] == 'Q') -- card[1][12];
			else if (temp[0] == 'K') -- card[1][13];
			else if (temp[0] == 'A') -- card[1][14];
			else if (temp[0] == '2') -- card[1][15];
			else if (temp[0] == 's') -- card[1][16];
			else -- card[1][17];
			cin >> temp;
		}
		cout << "Which means(index of your card type,begin,number of series if it is):";
		cin >> cardType >> beg >> num;
		++ beg;
		
		cout << "After your move:" << endl;
		cout << "Com:";
		for (int i=17;i>=3;--i)
			for (int j=0;j<card[0][i];++j)
				numTocard(i);
		cout << endl << "Ply:";
		for (int i=17;i>=3;--i)
			for (int j=0;j<card[1][i];++j)
				numTocard(i);
		cout << endl;
	}
}
bool determine(int depth, int cardType, int beg, int num, bool canPass = true)
{//博弈树决策 
	const int player = depth % 2;
	if (isEmpty(1-player)) return false;
	bool ans = false;
	
	if (cardType == 0)//一方要不起或者刚开局	
	{//判断当前状况是否已被搜索与记录过 
		dpHash dpHashNow = hashCalc(player);
		if (depth > 0)//如果不要求给出具体出牌内容 
		{
			for (int i=0;i<2;++i)
				if (dp[i].find(dpHashNow) != dp[i].end())
					return i;
		}
		for (int i=10;i>=6;--i)//尝试各种可出的牌
			if (typeAllowed[i])
			{
				for (int j=14-i;j>=leastSeries[i-5];--j)
				{ 
					ans = determine(depth, i, 3, j, false);
					if (ans) return hashRecord(dpHashNow, true);
					else if (depth == 0)
						cout << "(Type " << i << ", length " << j << ") is not OK." << endl;
				}
			}
		for (int i=5;i>=1;--i)
			if (typeAllowed[i])
			{
				ans = determine(depth, i, 3, 1, false);
				if (ans) return hashRecord(dpHashNow, true);
				else if (depth == 0)
					cout << "(Type " << i << ", length 1) is not OK." << endl;
			}
		for (int i=12;i>=11;--i)
			if (typeAllowed[i])
			{
				ans = determine(depth, i, 3, 1, false);
				if (ans) return hashRecord(dpHashNow, true);
				else if (depth == 0)
					cout << "(Type " << i << ", length 1) is not OK." << endl;
			}//有一种出法可以先手胜则为先手胜 
		return hashRecord(dpHashNow, false);//否则为后手胜 
	}
	else if (cardType <= 3)//以下每段内容类似 
	{
		for (int i=beg;i<=17;++i)
			if (card[player][i] >= cardType)
			{
				card[player][i] -= cardType;
				ans = !determine(depth+1, cardType, i+1, num);
				if (ans && depth == 0) newCardRecord();//记录出完后剩下的牌 
				card[player][i] += cardType;
				if (ans) return true;
			}//出不起相同牌型或出后赢不了，则将全部希望托付给炸弹 
		return canPass ? determine(depth, 11, 3, 1) : false;
	} 
	else if (cardType <= 5)
	{
		for (int i=beg;i<=17;++i)
		{
			if (card[player][i] >= 3)
			{
				card[player][i] -= 3;
				for (int j=3;j<=17;++j)
				{
					if (card[player][j] >= cardType-3)
					{
						card[player][j] -= cardType-3;
						ans = !determine(depth+1, cardType, i+1, num);
						if (ans && depth == 0) newCardRecord();
						card[player][j] += cardType-3;
						if (ans) break;
					}
				}
				card[player][i] += 3;
				if (ans) return true;
			}
		}
		return canPass ? determine(depth, 11, 3, 1) : false;
	}
	else if (cardType <= 8)
	{
		for (int i=beg;i<=14-num+1;++i)
			if (hasSeries(player, cardType-5, i, num))
			{
				subSeries(player, cardType-5, i, num);
				ans = !determine(depth+1, cardType, i+1, num);
				if (ans && depth == 0) newCardRecord();
				addSeries(player, cardType-5, i, num);
				if (ans) return true;
			}
		return canPass ? determine(depth, 11, 3, 1) : false;
	}
	else if (cardType <= 10)
	{
		for (int i=beg;i<=14-num+1;++i)
			if (hasSeries(player, 3, i, num))
			{
				subSeries(player, 3, i, num);//先确定三张的顺子 
				ans = attachFinder(depth, cardType, i+1, num, 
					3, num);//再递归尝试每一组三张所带的牌	
				addSeries(player, 3, i, num);
				if (ans) return true;
			}
		return canPass ? determine(depth, 11, 3, 1) : false;
	}
	else if (cardType == 11)
	{
		for (int i=beg;i<=15;++i)//普通炸弹 
			if (card[player][i] >= 4)
			{
				card[player][i] -= 4;
				ans = !determine(depth+1, cardType, i+1, num);
				if (ans && depth == 0) newCardRecord();
				card[player][i] += 4;
				if (ans) return true;
			}
		if (beg<=15 && hasSeries(player, 1, 16, 2))//大小鬼 
		{
			subSeries(player, 1, 16, 2);
			ans = !determine(depth+1, cardType, 16, num);
			if (ans && depth == 0) newCardRecord();
			addSeries(player, 1, 16, 2);
			if (ans) return true;
		}
		if (depth == 0) newCardRecord();
		return canPass ? !determine(depth+1, 0, 0, 0) : false;//彻底要不起 
	}
	else
	{
		for (int i=beg;i<=17;++i)
		{
			if (card[player][i] >= 4)
			{
				card[player][i] -= 4;
				for (int j=3;j<=17;++j)
				for (int k=j;k<=17;++k)
				{
					if (j!=k && card[player][j]>=1 && card[player][k]>=1
						|| j==k && card[player][j]>=2)
					{
						-- card[player][j];
						-- card[player][k];
						ans = !determine(depth+1, cardType, i+1, num);
						if (ans && depth == 0) newCardRecord();
						++ card[player][j];
						++ card[player][k];
						if (ans) break;
					}
				}
				card[player][i] += 4;
				if (ans) return true;
			}
		}
		return canPass ? determine(depth, 11, 3, 1) : false;
	}
}
bool attachFinder(int depth, int cardType, int beg, int num, 
					int index, int rest)
{
	const int player = depth % 2;
	if (rest == 0)//递归找齐后进行尝试 
	{
		bool ans = !determine(depth+1, cardType, beg, num);
		if (ans && depth == 0) newCardRecord();
		return ans;
	}
	else
	{
		for (int i=index;i<=17;++i)
			if (card[player][i] >= cardType-8)
			{
				card[player][i] -= cardType-8;
				bool ans = attachFinder(depth, cardType, beg, num,
					i, rest-1);
				card[player][i] += cardType-8;
				if (ans) return true;//有一组能行则停止 
			}
		return false;
	}
}
void flagInit()
{
	for (int player=0;player<2;++player)
		for (int cardType=6;cardType<=8;++cardType)
			for (int i=3;i<=14;++i)
				for (int num=14-i+1;num>=2;--num)
				{
					flagSeries[player][cardType-5][i][num] = true;
					flagSeries[player][cardType-5][i][num] =
						hasSeries(player, cardType-5, i, num);
				}
}
void landlords()
{
	int cardType = 0, beg = 0, num = 0;
	char isComFirst;
	cout << "Does the computer move first?(y for yes ans n for no):";
	cin >> isComFirst;
	if (isComFirst == 'n') ply(cardType, beg, num);

	flagInit();
	while (true)
	{
		bool ans = determine(0, cardType, beg, num);
		if (ans)
		{
			com();
			ply(cardType, beg, num);
		}
		else
		{
			cout << "The computer surrenders.You win!" << endl;
			system("pause");
			exit(0);
		}
	}
}
int main()
{
	gameset(); 
	landlords();
	return 0;
} 
