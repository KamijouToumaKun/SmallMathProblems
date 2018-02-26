#include <ctime>
#include <fstream>
using namespace std;
ifstream fin("sudoku.txt");
ofstream fout("result.txt");
struct sudoku
{
	int num;					//��������֣�0Ϊδ�� 
	bool occu[9];				//����������й�ÿ�������Ƿ��Ѿ����� 
	int occunum;				//�������й��Ѿ����ڵ����ָ��� 
}array[9][9];
const int rank[9][9] = 			//�Ź����� 
{
	0,0,0,1,1,1,2,2,2,
	0,0,0,1,1,1,2,2,2,
	0,0,0,1,1,1,2,2,2,
	3,3,3,4,4,4,5,5,5,
	3,3,3,4,4,4,5,5,5,
	3,3,3,4,4,4,5,5,5,
	6,6,6,7,7,7,8,8,8,
	6,6,6,7,7,7,8,8,8,
	6,6,6,7,7,7,8,8,8,
};
void fillin(int i, int j, int n);//��ָ��λ������ָ�����������Ҹ����������й��������ֵĺ�ѡ��Χ 
bool onlynum();					 //Ψһ��������һ����λ�������й��Ѿ���8�������ù��ˣ��������λȷ�� 
bool onlyoccu();				 //����Ψһ��������һ����λ�����л��л���ֻ�����п�������һ�������������λȷ��

int chain[81][2];				 //��������occunumΪָ������n�Ŀ�λ
int top;						 //chain��������
bool chainoccu(int n);			 //ͳ������occunumΪָ������n�Ŀ�λ������chain�� 
int temp[9];					 //����C(top, 9-n)�������������
bool chainsear(int n, int index, int step);//����chain������(9-n)Ԫ��
								 //����������ҲΪ(9-n) �������ͬ���л��л���������λ���⼸����ѡ�� 
int checksame(int n);			 //�ж�(9-n)Ԫ���Ԫ���Ƿ�ͬ�л��л�
bool common[9];					 //����chain��ÿһ��(9-n)Ԫ��ĺ�ѡ���Ľ���

void suppose();					 //������ 
clock_t start;					 //��¼����ʱ�� 

void fillin(int i, int j, int n)
{
	int k, l;
	array[i][j].num = n+1;
	array[i][j].occunum = 9;
	for (k=0;k<9;k++)//���и��� 
	{
	  	if (!array[i][k].num && !array[i][k].occu[n])
	  	{
			array[i][k].occu[n] = true;
			array[i][k].occunum ++;
	    }
		if (!array[k][j].num && !array[k][j].occu[n])
	  	{
			array[k][j].occu[n] = true;
			array[k][j].occunum ++;
	    }
	}
	for (k=0;k<9;k++)//�Ź�����
	  for (l=0;l<9;l++)
	    if (rank[k][l] == rank[i][j] && !array[k][l].num
			&& !array[k][l].occu[n])
		{
			array[k][l].occu[n] = true;
			array[k][l].occunum ++;
		}
}

bool onlynum()
{
	int i, j, k, l;
	for (i=0;i<9;i++)
	  for (j=0;j<9;j++)
	    if (array[i][j].occunum == 8)
	    {
	    	for (k=0;k<9;k++)
	    	  if (!array[i][j].occu[k]) break;
	    	fillin(i, j, k);
			return true;
		}
	return false;
}

bool onlyoccu()
{
	int i, j, k, l, n, num1, num2;
	for (n=0;n<9;n++)//����������� 
	{
		for (i=0;i<9;i++)//ÿһ��
		{
			num1 = -1;
			for (j=0;j<9;j++)
			  if (!array[i][j].num && !array[i][j].occu[n])
			  {
			  	  if (num1 < 0) num1 = j;
			  	  else break;
			  }
			if (num1 > 0 && j == 9)//�ж��Ƿ�ǡ��һ�� 
			{
				fillin(i, num1, n);
				return true;
			}
		}
		for (j=0;j<9;j++)//ÿһ�� 
		{
			num1 = -1;
			for (i=0;i<9;i++)
			  if (!array[i][j].num && !array[i][j].occu[n])
			  {
			  	  if (num1 < 0) num1 = i;
			  	  else break;
			  }
			if (num1 > 0 && i == 9)
			{
				fillin(num1, j, n);
				return true;
			}
		}
		for (i=1;i<=3;i++)//ÿ���Ź�
		  for (j=1;j<=3;j++)
		  {
			  num1 = -1;
		  	  for (k=3*(i-1);k<3*i;k++)//����ÿһ���Ź� 
	        	for (l=3*(j-1);l<3*j;l++)
	        	  if (!array[k][l].num && !array[k][l].occu[n])
	        	  {
	        	  	  if (num1 < 0)
					  {
						  num1 = k;
						  num2 = l;
					  }
					  else goto squarewrong;
				  }
			  squarewrong:
	          if (num1 > 0 && k == 3*i)
			  {
				  fillin(num1, num2, n);
				  return true;
			  }
		  }
	}
	return false;
}

int checksame(int n)
{
	int i;
	for (i=0;i<8-n;i++)//ͬ�� 
	  if (chain[temp[i]][0] != chain[temp[i+1]][0]) break;
	if (i == 8-n) return 1;
	
	for (i=0;i<8-n;i++)//ͬ�� 
	  if (chain[temp[i]][1] != chain[temp[i+1]][1]) break;
	if (i == 8-n) return 2;
	
	for (i=0;i<8-n;i++)//ͬ�Ź� 
	  if ( rank[chain[temp[i]][0]][chain[temp[i]][1]] != 
		  rank[chain[temp[i+1]][0]][chain[temp[i+1]][1]] ) break;
	if (i == 8-n) return 3;
	return 0;
}

bool chainsear(int n, int index, int step)
{
	int i, j, k, l, m, style, count;
	if (step == 9-n)
	{
		if (! (style = checksame(n))) return false;//Ҫ��ͬ�л��л� 
		for (i=0;i<9;i++) 
		{
			common[i] = false;
			for (j=0;j<9-n;j++)
		      common[i] = common[i] ||
			  	!array[chain[temp[j]][0]][chain[temp[j]][1]].occu[i];
		}//�󽻼� 
		count = 0;
		for (i=0;i<9;i++)
		  if (common[i]) count ++;
		if (count == 9-n)//����Ԫ��Ҳǡ��(9-n)�� 
		{
			bool flag = false;
			switch (style)
			{
				case 1://ͬ�� 
					for (i=0;i<9;i++)
					{
						if (array[chain[temp[0]][0]][i].num) continue;
						for (j=0;j<9-n;j++)
						  if (i == chain[temp[j]][1]) break;
						if (j == 9-n)//�ж�����ͬ���л��л���������λ
						{
							for (j=0;j<9;j++)
							  if (common[j] && !array[chain[temp[0]][0]][i].occu[j])
							  {//�ɲ����ĺ�ѡ����δ���� 
							  	  flag = true;
							  	  array[chain[temp[0]][0]][i].occu[j] = true;
							  	  array[chain[temp[0]][0]][i].occunum ++;
							  }
						}
					}break;
				case 2://ͬ�� 
					for (i=0;i<9;i++)
					{
						if (array[i][chain[temp[0]][1]].num) continue;
						for (j=0;j<9-n;j++)
						  if (i == chain[temp[j]][0]) break;
						if (j == 9-n)
						{
							for (j=0;j<9;j++)
							  if (common[j] && !array[i][chain[temp[0]][1]].occu[j])
							  {
							  	  flag = true;
							  	  array[i][chain[temp[0]][1]].occu[j] = true;
							  	  array[i][chain[temp[0]][1]].occunum ++;
							  }
						}
					}break;
				case 3://ͬ�Ź� 
					i = rank[chain[temp[0]][0]][chain[temp[0]][1]] / 3 + 1;
					j = rank[chain[temp[0]][0]][chain[temp[0]][1]] % 3 + 1;
					for (k=3*(i-1);k<3*i;k++)//�����Ź� 
	        		  for (l=3*(j-1);l<3*j;l++)
					  {
						  if (array[k][l].num) continue;
						  for (m=0;m<9-n;m++)
						    if (k == chain[temp[m]][0] && l == chain[temp[m]][1])
							  break;
						  if (m == 9-n)
						  {
							for (m=0;m<9;m++)
							  if (common[m] && !array[k][l].occu[m])
							  {
							  	  flag = true;
							  	  array[k][l].occu[m] = true;
							  	  array[k][l].occunum ++;
							  }
						}
					  }break;
			}
			return flag;
		}
		else return false;//Ҫ������Ϊ�ŷ���true 
	}
	else
	{
		for (i=index;i<top+n-8+step;i++)//�ݹ鹹��(9-n)Ԫ�� 
		{
			temp[step] = i;
			if (chainsear(n, i+1, step+1)) return true;//��һ��ɹ��ͷ���true����ʱֹͣ 
		}
		return false;
	}
}

bool chainoccu(int n)
{
	int i, j;
	top = 0;
	for (i=0;i<9;i++)
	  for (j=0;j<9;j++)
	    if (!array[i][j].num && array[i][j].occunum >= n)
	    {
			chain[top][0] = i;
			chain[top][1] = j;
			top ++;
		}
	if (top >= 9-n) return chainsear(n, 0, 0);
	else return false;
}

void suppose()
{
	int i, j, k, l, m, n;
	for (i=0;i<9;i++)//�ҵ���һ����λ 
	  for (j=0;j<9;j++)
	    if (!array[i][j].num)
		  goto supposeblank;
	supposeblank:
	if (i == 9)//û�п�λ��ȫ��������� 
	{
		for (i=0;i<9;i++)//��� 
		{
			for (j=0;j<9;j++)
			  fout << array[i][j].num << " ";
			fout << endl;
		}
		fout << "Time: " << clock()-start << "ms." << endl;
		exit(0);//�н⼴Ψһ�⣬�������� 
		//���������ﲻֹͣ���򣬵�����λ������ٵݹ��������������Է�ֹ�ظ���Ѱ�Ҷ�� 
	}
	
	sudoku t[9][9];
	for (k=0;k<9;k++)
	  for (l=0;l<9;l++)
	    t[k][l] = array[k][l];//���� 
	for (k=0;k<9;k++)
	  if (!array[i][j].occu[k])
	  {
	  	  fillin(i, j, k);//�ڿ�λ�����ѡ�� 
		  while ( onlynum() || onlyoccu()//����ʹ����������ֱ��ȫ��Ч�� 
			|| chainoccu(7) ) ;
	  	  for (l=0;l<9;l++)
	  	    for (m=0;m<9;m++)
	  	      if (!array[l][m].num)
	  	      {
	  	      	  for (n=0;n<9;n++)
	  	      	    if (!array[l][m].occu[n]) break;
	  	      	  if (n == 9)//�п�λû��һ����ѡ���������費���� 
					goto supposewrong;
			  }
		  suppose();//��ʱû��ì�ܣ��ݹ�����һ����λ 
		  supposewrong:
		  for (l=0;l<9;l++)
	  	    for (m=0;m<9;m++)
	  	      array[l][m] = t[l][m];//���ƻ�����������һ�ֿ��� 
	  }
}

int main()
{
	start = clock();
	int i, j, k, l;
	
	for (i=0;i<9;i++)
	  for (j=0;j<9;j++)
	  {
	  	  fin >> array[i][j].num;
	  	  for (k=0;k<9;k++)
	  	    array[i][j].occu[k] = false;
	  	  array[i][j].occunum = 0;
	  }
	for (i=0;i<9;i++)
	  for (j=0;j<9;j++)
	  {
	  	  if (array[i][j].num) array[i][j].occunum = 9;
	  	  else//������ͳ�Ƹ���λ��occu 
	  	  {
			  for (k=0;k<9;k++)//���� 
			  {
			  	  if (array[i][k].num)
					array[i][j].occu[array[i][k].num-1] = true;
			  	  if (array[k][j].num)
					array[i][j].occu[array[k][j].num-1] = true;
			  }
			  for (k=0;k<9;k++)//�Ź�
			    for (l=0;l<9;l++)
			      if (rank[k][l] == rank[i][j] && array[k][l].num)
				    array[i][j].occu[array[k][l].num-1] = true;
			  for (k=0;k<9;k++)//ͳ��occunum 
				if (array[i][j].occu[k])
				  array[i][j].occunum ++;
		  }
	  }
	while ( onlynum() || onlyoccu()//����ʹ�����Ϸ���ֱ��ȫ��Ч�� 
		|| chainoccu(7) ) ;
	suppose();
	return 0;
}
