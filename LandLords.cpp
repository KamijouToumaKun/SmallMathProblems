#include <set>
#include <fstream>
#include <iostream>
using namespace std;
/*
A = 14, 2 = 15, s(mall joker) = 16, b(ig joker) = 17
0��Ҫ����
1���� 2��˫ 3���� 4������һ 5��������
6����˳ 7��˫˳ 8����˳ 9������һ˳ 10��������˳
11��ը�� 12���Ĵ���
gameset.txt ��һ��ȷ������12�ֹ��� �ڶ�����д�����������
���ִ�Сд ����˳�� ��0��β 

Ŀǰû���ҵ����õ�hash��������
*/ 
struct dpHash//��һ��Ҫ������߿��ֵ�ʱ�򣬶Գ���˫�����͵ļ�¼ 
{
	int player;//���з� 
	long long cardHash[2];//˫�����͵������״̬ѹ�� 
	inline friend bool operator <(dpHash x, dpHash y)
	{
		if (x.player != y.player) return x.player < y.player;
		else if (x.cardHash[0] != y.cardHash[0]) return x.cardHash[0] < y.cardHash[0];
		else return x.cardHash[1] < y.cardHash[1];
	}
};
set <dpHash> dp[2];//���仯���� 
int card[2][18], newCard[2][18];//��ǰ���������Ԥ���ڱ��ֳ�������µ��� 
bool typeAllowed[13];//ȷ��������Щ���� 
const int leastSeries[6] = {0,5,3,2,2,2};//�������������ϲ���˳�� 
bool flagSeries[2][4][18][16];
const long long five[18] = {0,0,0,1,5,25,125,625,3125,15625,78125,390625,1953125,9765625,
			48828125,244140625,1220703125,6103515625};
bool attachFinder(int depth, int cardType, int beg, int num, 
					int index, int rest);//���ڵݹ黥����ã������� 

inline bool isEmpty(int player)//�ж�һ�������Ƿ��Ѵ��� 
{
	for (int i=3;i<=17;++i)
		if (card[player][i]) return false;
	return true;
}
inline bool hasSeries(int player, int cardNum, int beg, int num)
{//�ж�һ���Ƿ���ĳ�ִ�ĳ���ƿ�ʼ��˳�� 
	if (!flagSeries[player][cardNum][beg][num]) return false;

	for (int i=0;i<num;++i)
		if (card[player][beg+i] < cardNum) return false;
	return true;
}
inline void subSeries(int player, int cardNum, int beg, int num)
{//���˳�� 
	for (int i=0;i<num;++i)
		card[player][beg+i] -= cardNum;
}
inline void addSeries(int player, int cardNum, int beg, int num)
{//��ԭ˳�� 
	for (int i=0;i<num;++i)
		card[player][beg+i] += cardNum;
}
inline void newCardRecord()//��¼�µ���Ԥ���ڱ��ֳ�������µ��� 
{
	for (int i=0;i<2;++i)
		for (int j=3;j<=17;++j)
			newCard[i][j] = card[i][j];
}
inline void numTocard(int num)//����� 
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
dpHash hashCalc(int player)//��ǰ����hash�� 
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
inline bool hashRecord(dpHash dpHashNow, bool ans)//��������ļ�¼ 
{
	dp[ans].insert(dpHashNow);
	return ans;
}
void gameset()//��Ϸ���ֵ����� 
{
	cout << "Make sure you have written down your own setting in gameset.txt." << endl; 
	cout << "Determine the rules you adopt of the 12 in the 1st line." << endl;
	cout << "The 2nd line consists of the cards of computer,ending with 0." << endl;
	cout << "The 3rd line consists of the cards of player,ending with 0." << endl;
	cout << "Both are case sensitive.Here s is for small joker while b is for big one." << endl;
	cout << "Game starts!" << endl << endl;
	
	ifstream fin("gameset.txt");
	for (int i=1;i<13;++i)//������� 
		fin >> typeAllowed[i];
	for (int i=0;i<2;++i)//����˫�����ͣ���0���� 
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
	cout << "Com:";//���˫������ 
	for (int i=17;i>=3;--i)
		for (int j=0;j<card[0][i];++j)
			numTocard(i);
	cout << endl << "Ply:";
	for (int i=17;i>=3;--i)
		for (int j=0;j<card[1][i];++j)
			numTocard(i);
	cout << endl;
}
void com()//���Գ��� 
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
void ply(int &cardType, int &beg, int &num)//������ƣ��������м�¼�³�����Ϣ 
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
{//���������� 
	const int player = depth % 2;
	if (isEmpty(1-player)) return false;
	bool ans = false;
	
	if (cardType == 0)//һ��Ҫ������߸տ���	
	{//�жϵ�ǰ״���Ƿ��ѱ��������¼�� 
		dpHash dpHashNow = hashCalc(player);
		if (depth > 0)//�����Ҫ���������������� 
		{
			for (int i=0;i<2;++i)
				if (dp[i].find(dpHashNow) != dp[i].end())
					return i;
		}
		for (int i=10;i>=6;--i)//���Ը��ֿɳ�����
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
			}//��һ�ֳ�����������ʤ��Ϊ����ʤ 
		return hashRecord(dpHashNow, false);//����Ϊ����ʤ 
	}
	else if (cardType <= 3)//����ÿ���������� 
	{
		for (int i=beg;i<=17;++i)
			if (card[player][i] >= cardType)
			{
				card[player][i] -= cardType;
				ans = !determine(depth+1, cardType, i+1, num);
				if (ans && depth == 0) newCardRecord();//��¼�����ʣ�µ��� 
				card[player][i] += cardType;
				if (ans) return true;
			}//��������ͬ���ͻ����Ӯ���ˣ���ȫ��ϣ���и���ը�� 
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
				subSeries(player, 3, i, num);//��ȷ�����ŵ�˳�� 
				ans = attachFinder(depth, cardType, i+1, num, 
					3, num);//�ٵݹ鳢��ÿһ��������������	
				addSeries(player, 3, i, num);
				if (ans) return true;
			}
		return canPass ? determine(depth, 11, 3, 1) : false;
	}
	else if (cardType == 11)
	{
		for (int i=beg;i<=15;++i)//��ͨը�� 
			if (card[player][i] >= 4)
			{
				card[player][i] -= 4;
				ans = !determine(depth+1, cardType, i+1, num);
				if (ans && depth == 0) newCardRecord();
				card[player][i] += 4;
				if (ans) return true;
			}
		if (beg<=15 && hasSeries(player, 1, 16, 2))//��С�� 
		{
			subSeries(player, 1, 16, 2);
			ans = !determine(depth+1, cardType, 16, num);
			if (ans && depth == 0) newCardRecord();
			addSeries(player, 1, 16, 2);
			if (ans) return true;
		}
		if (depth == 0) newCardRecord();
		return canPass ? !determine(depth+1, 0, 0, 0) : false;//����Ҫ���� 
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
	if (rest == 0)//�ݹ��������г��� 
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
				if (ans) return true;//��һ��������ֹͣ 
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
