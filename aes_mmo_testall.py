import gurobipy as gp
from gurobipy import GRB

XOR_RULE = [[0,-1,0,-1,0,2,-3,-1,1],
[-1,0,-1,0,2,0,-1,-3,1],
[0,1,0,1,0,-2,2,0,0],
[1,0,1,0,-2,0,0,2,0],
[2,2,0,0,-1,-1,0,0,0]]

def modeltmp(model,inputs,rules):
    if len(inputs) != len(rules[0])-1:
        print(len(inputs))
        print("error")
        exit()
    for r in rules:
        expr = 0
        for i in range(0,len(r)-1):
            expr += r[i]*inputs[i]
        model.addConstr(expr + r[-1] >= 0)
        

def modelxor(model,a,b,c,xorc):
    model.addConstr(a + b - c >= 0)
    model.addConstr(a - b + c >= 0)
    model.addConstr(- a + b + c >= 0)
    model.addConstr(-c - xorc +1 >= 0)
    model.addConstr(b - xorc >= 0)
    model.addConstr(a - xorc >= 0)
    model.addConstr(-a +c -b + xorc + 1 >= 0)

def modelstatexor(model,input1,input2,output,xorc):
    for i in range(0,len(input1)):
        modelxor(model,input1[i],input2[i],output[i],xorc[i])

def modelmc(model,inputcol,outputcol,COL,mcc):
    temp = model.addVar(vtype=GRB.BINARY)
    expr = 0
    for i in inputcol+outputcol:
        model.addConstr(temp - i >= 0)
        expr += i
    model.addConstr(expr >= (COL+1)*temp)
    expr1 = 0
    for i in outputcol:
        expr1 += i
    model.addConstr(mcc == COL*temp - expr1)


def modelstatemc(model,inputstate,outputstate,COL,mcc):
    for j in range(0,4):
        modelmc(model,[inputstate[COL*j+i] for i in range(0,COL)],[outputstate[COL*j+i] for i in range(0,COL)],COL,mcc[j])

def substates_shiftrow(substates,COL):
    ans = []
    for j in range(0,4):
        for i in range(0,COL):
            ans.append(substates[(COL*j+(COL+1)*i)%(4*COL)])
    return ans

def printstate(state):
    for i in range(0,4):
        print(state[0+i], state[4+i], state[8+i], state[12+i])

def chulistate(inputstate):
    ans = []
    for i in range(0,len(inputstate)):
        if inputstate[i] == 0:
            ans.append("W")
        elif inputstate[i] == 1:
            ans.append("B")
        elif inputstate[i] == 2:
            ans.append("R")
        elif inputstate[i] == 3:
            ans.append("G")
        else:
            ans.append("error")
    return ans

def MC_con(model,input_col_blue,input_col_red,input_col_white,output_col_blue,output_col_red,consume_blue,consume_red): #using method from crypto2022 baozhenzhen
    exist_white = model.addVar(vtype=GRB.BINARY)
    all_blue_gray = model.addVar(vtype=GRB.BINARY)
    all_red_gray = model.addVar(vtype=GRB.BINARY)

    sum_input_white = 0
    for i in range(0,len(input_col_white)):
        sum_input_white += input_col_white[i]
    model.addConstr(4*exist_white - sum_input_white >= 0)
    model.addConstr(exist_white - sum_input_white <= 0)


    sum_input_blue = 0
    for i in range(0,len(input_col_blue)):
        sum_input_blue += input_col_blue[i]
    model.addConstr(sum_input_blue - 4*all_blue_gray >= 0)
    model.addConstr(sum_input_blue - all_blue_gray <= 3)

    sum_input_red = 0
    for i in range(0,len(input_col_red)):
        sum_input_red += input_col_red[i]
    model.addConstr(sum_input_red - 4*all_red_gray >= 0)
    model.addConstr(sum_input_red - all_red_gray <= 3)

    sum_output_blue = 0
    for i in range(0,len(output_col_blue)):
        sum_output_blue += output_col_blue[i]
    model.addConstr(sum_output_blue + 4*exist_white <= 4)
    model.addConstr(sum_output_blue + sum_input_blue - 8*all_blue_gray >=0)
    model.addConstr(sum_output_blue + sum_input_blue - 5*all_blue_gray <= 8-5)

    sum_output_red = 0
    for i in range(0,len(output_col_red)):
        sum_output_red += output_col_red[i]
    model.addConstr(sum_output_red + 4*exist_white <= 4)
    model.addConstr(sum_output_red + sum_input_red - 8*all_red_gray >=0)
    model.addConstr(sum_output_red + sum_input_red - 5*all_red_gray <= 8-5)

    model.addConstr(sum_output_red - 4*all_red_gray - consume_blue == 0)
    model.addConstr(sum_output_blue - 4*all_blue_gray - consume_red == 0)

def Match_con(model,input_col_white,output_col_white,match_ability):
    sum_input_white = 0
    for i in range(0,len(input_col_white)):
        sum_input_white += input_col_white[i]
    sum_output_white = 0
    for i in range(0,len(output_col_white)):
        sum_output_white += output_col_white[i]
    temp = model.addVar(vtype=GRB.INTEGER)
    model.addConstr(temp == 4 - sum_input_white - sum_output_white)
    model.addConstr(match_ability== gp.max_(temp,0))

def SR_get(inputstate):
    ans = []
    for i in range(0,16):
        ans.append(inputstate[(4*(i%4)+i)%16])
    return ans
def COL_get(inputstate,col):
    ans = []
    for i in range(0,4):
        ans.append(inputstate[4*col + i])
    return ans

def nostradamus(ROUNDS,initial_round,match_round,TD,quantum):
    m = gp.Model("AES-MMO_Nostradamus")
    m.Params.Threads = 4

    COL = 4
    ROW = 4
   
    initial_degree_forward = m.addVar(vtype=GRB.INTEGER, name="initial_degree_forward")
    initial_degree_backward = m.addVar(vtype=GRB.INTEGER, name="initial_degree_backward")
    blue = m.addVars(ROUNDS,ROW*COL,vtype=GRB.BINARY, name="blue") #Blue Forward
    red = m.addVars(ROUNDS,ROW*COL,vtype=GRB.BINARY, name="red") #Red Backward
    gray = m.addVars(ROUNDS,ROW*COL,vtype=GRB.BINARY, name="gray")
    white = m.addVars(ROUNDS,ROW*COL,vtype=GRB.BINARY, name="white")
    consume_blue = m.addVars(ROUNDS,COL,vtype=GRB.INTEGER, name="consume_blue") #Consume Blue
    consume_red = m.addVars(ROUNDS,COL,vtype=GRB.INTEGER, name="consume_red") #Consume Red
    match_ability = m.addVars(COL,vtype=GRB.INTEGER, name="match_ability")
    target_blue = m.addVars(ROW*COL,vtype=GRB.BINARY, name="target_blue")
    target_red = m.addVars(ROW*COL,vtype=GRB.BINARY, name="target_red")
    target_gray = m.addVars(ROW*COL,vtype=GRB.BINARY, name="target_gray")
    target_degree_blue = m.addVars(ROW*COL,vtype=GRB.BINARY, name="target_degree_blue")
    target_degree_red = m.addVars(ROW*COL,vtype=GRB.BINARY, name="target_degree_red")
    target_consume_blue = m.addVars(ROW*COL,vtype=GRB.BINARY, name="target_consume_blue")
    target_consume_red = m.addVars(ROW*COL,vtype=GRB.BINARY, name="target_consume_red")
    objective = m.addVar(vtype=GRB.INTEGER, name="objective")
    
    for i in range(0,ROW*COL):
        m.addConstr(target_blue[i] - target_gray[i] >= 0)
        m.addConstr(target_red[i] - target_gray[i] >= 0)
        m.addConstr(target_blue[i] + target_red[i] - 2*target_gray[i] <= 1)
    for i in range(0,ROW*COL):
        m.addConstr(target_degree_blue[i] <= target_blue[i])
        m.addConstr(target_degree_blue[i] <= 1 - target_red[i] )
        m.addConstr(target_degree_red[i] <= target_red[i])
        m.addConstr(target_degree_red[i] <= 1 - target_blue[i] )

    target_degree_red_sum = 0
    target_degree_blue_sum = 0
    for i in range(0,ROW*COL):
        target_degree_red_sum += target_degree_red[i]
        target_degree_blue_sum += target_degree_blue[i]
    m.addConstr(target_degree_red_sum + target_degree_blue_sum <= TD)

    
    #Red Blue Gray Constraints
    for r in range(0,ROUNDS):
        for i in range(0,ROW*COL):
            m.addConstr(blue[r,i] - gray[r,i] >= 0)
            m.addConstr(red[r,i] - gray[r,i] >= 0)
            m.addConstr(blue[r,i] + red[r,i] - 2*gray[r,i] <= 1)
    #Red Blue White Constraints
    for r in range(0,ROUNDS):
        for i in range(0,ROW*COL):
            m.addConstr(white[r,i] + blue[r,i] + red[r,i] >= 1)
            m.addConstr(white[r,i] <= 1 - red[r,i])
            m.addConstr(white[r,i] <= 1 - blue[r,i])
    
    #Constraints for initial degree
    temp = 0
    for i in range(0,ROW*COL):
        temp += blue[initial_round,i] - gray[initial_round,i]
    m.addConstr(initial_degree_forward == temp)

    temp = 0
    for i in range(0,ROW*COL):
        temp += red[initial_round,i] - gray[initial_round,i]
    m.addConstr(initial_degree_backward == temp)
    
    blue_state_S = [[blue[r,i] for i in range(0,ROW*COL)]for r in range(0,ROUNDS)]
    red_state_S = [[red[r,i] for i in range(0,ROW*COL)]for r in range(0,ROUNDS)]
    # gray_state_S = [[gray[r,i] for i in range(0,ROW*COL)]for r in range(0,ROUNDS)]
    white_state_S = [[white[r,i] for i in range(0,ROW*COL)]for r in range(0,ROUNDS)]
    
    if match_round>=initial_round:
        for r in range(0,initial_round):
            SR_state_blue = SR_get(blue_state_S[r])
            SR_state_red = SR_get(red_state_S[r])
            SR_state_white = SR_get(white_state_S[r])
            for col in range(0,4):
                MC_con(m,COL_get(blue_state_S[r+1],col), COL_get(red_state_S[r+1],col), COL_get(white_state_S[r+1],col), COL_get(SR_state_blue,col), COL_get(SR_state_red,col),  consume_blue[r,col], consume_red[r,col])
        
        for r in range(initial_round,match_round):
            SR_state_blue = SR_get(blue_state_S[r])
            SR_state_red = SR_get(red_state_S[r])
            SR_state_white = SR_get(white_state_S[r])
            for col in range(0,4):
                MC_con(m,COL_get(SR_state_blue,col), COL_get(SR_state_red,col), COL_get(SR_state_white,col), COL_get(blue_state_S[r+1],col), COL_get(red_state_S[r+1],col), consume_blue[r,col], consume_red[r,col])
        
        for r in range(match_round+1,ROUNDS-1):
            SR_state_blue = SR_get(blue_state_S[r])
            SR_state_red = SR_get(red_state_S[r])
            SR_state_white = SR_get(white_state_S[r])
            for col in range(0,4):
                MC_con(m,COL_get(blue_state_S[r+1],col), COL_get(red_state_S[r+1],col), COL_get(white_state_S[r+1],col), COL_get(SR_state_blue,col), COL_get(SR_state_red,col),  consume_blue[r,col], consume_red[r,col])
        
        SR_state_blue = SR_get(blue_state_S[ROUNDS-1])
        SR_state_red = SR_get(red_state_S[ROUNDS-1])
        
        for i in range(0,ROW*COL):
            modeltmp(m,[blue_state_S[0][i],red_state_S[0][i],target_blue[i],target_red[i],SR_state_blue[i],SR_state_red[i],target_consume_blue[i],target_consume_red[i]],XOR_RULE)
    else:
        for r in range(0,match_round):
            SR_state_blue = SR_get(blue_state_S[r])
            SR_state_red = SR_get(red_state_S[r])
            SR_state_white = SR_get(white_state_S[r])
            for col in range(0,4):
                MC_con(m,COL_get(SR_state_blue,col), COL_get(SR_state_red,col), COL_get(SR_state_white,col), COL_get(blue_state_S[r+1],col), COL_get(red_state_S[r+1],col), consume_blue[r,col], consume_red[r,col])
        for r in range(match_round+1,initial_round):
            SR_state_blue = SR_get(blue_state_S[r])
            SR_state_red = SR_get(red_state_S[r])
            SR_state_white = SR_get(white_state_S[r])
            for col in range(0,4):
                MC_con(m,COL_get(blue_state_S[r+1],col), COL_get(red_state_S[r+1],col), COL_get(white_state_S[r+1],col), COL_get(SR_state_blue,col), COL_get(SR_state_red,col),  consume_blue[r,col], consume_red[r,col])
        for r in range(initial_round,ROUNDS-1):
            SR_state_blue = SR_get(blue_state_S[r])
            SR_state_red = SR_get(red_state_S[r])
            SR_state_white = SR_get(white_state_S[r])
            for col in range(0,4):
                MC_con(m,COL_get(SR_state_blue,col), COL_get(SR_state_red,col), COL_get(SR_state_white,col), COL_get(blue_state_S[r+1],col), COL_get(red_state_S[r+1],col), consume_blue[r,col], consume_red[r,col])
        SR_state_blue = SR_get(blue_state_S[ROUNDS-1])
        SR_state_red = SR_get(red_state_S[ROUNDS-1])
        for i in range(0,ROW*COL):
            modeltmp(m,[SR_state_blue[i],SR_state_red[i],target_blue[i],target_red[i],blue_state_S[0][i],red_state_S[0][i],target_consume_blue[i],target_consume_red[i]],XOR_RULE)
    
    # Constraints for final degree
    match_L = SR_get(white_state_S[match_round])
    for col in range(0,COL):
        Match_con(m,COL_get(match_L,col), COL_get(white_state_S[match_round+1],col),match_ability[col])

 
    objective1 = initial_degree_forward + target_degree_blue_sum
    objective2 = initial_degree_backward + target_degree_red_sum

    for r in range(0,ROUNDS):
        for col in range(0,COL):
            objective1 = objective1 - consume_blue[r,col]
            objective2 = objective2 - consume_red[r,col]
    for i in range(0,ROW*COL):
        objective1 = objective1 - target_consume_blue[i]
        objective2 = objective2 - target_consume_red[i]

    objective3 = 0
    for col in range(0,COL):
        objective3 = objective3 + match_ability[col]

    if not quantum:
        temp = m.addVar(vtype=GRB.INTEGER)
        m.addConstr(temp <= objective1)
        m.addConstr(temp <= objective2)
        m.addConstr(temp <= objective3)
        m.addConstr((128+(target_degree_red_sum + target_degree_blue_sum)*8)/2 <= objective)
        m.addConstr(128 - 8*temp <= objective)
        m.setObjective(objective,GRB.MINIMIZE)
    else:
        temp = m.addVar(vtype=GRB.INTEGER)
        temp2 = m.addVar(vtype=GRB.INTEGER)
        temp3 = m.addVar(vtype=GRB.INTEGER)
        temp4 = m.addVar(vtype=GRB.INTEGER)
        m.addConstr(temp <= objective1/2)
        m.addConstr(temp <= objective2/2)
        m.addConstr(temp <= objective3/2)
        m.addConstr(temp3 == objective1 - objective2 + 5)
        m.addConstr(temp4 == objective2 - objective1 + 5)
        m.addConstr(temp2 == gp.max_(temp3,temp4))
        # m.addConstr(temp2 >= /2)
        m.addConstr(temp <=temp2/2 - 2.5)
        m.addConstr((128+(target_degree_red_sum + target_degree_blue_sum)*16)/3 <= objective)
        m.addConstr(64 - 8*temp <= objective)
        m.setObjective(objective,GRB.MINIMIZE)
    m.optimize()
    # # print objs
    # print(objective1.getValue(), objective2.getValue(), objective3.getValue(), objective.x)

    # print colored state
    state = []
    for r in range(0,ROUNDS):
        state.append([])
        for i in range(0,ROW*COL):
            state[r].append(int(blue[r,i].x+red[r,i].x*2+0.1))

    for r in range(0,ROUNDS):
        print("Round",r)
        printstate(chulistate(state[r]))

    # write attack complexity to ans.txt
    with open("ans.txt","a") as f:
        print(initial_round,match_round,objective.x,file = f)


if __name__ == '__main__':
    # # classical setting
    # for i in range(0,5):
    #     for j in range(0,5):
    #         nostradamus(6,i,j,int(16/3),False)
    #         exit()
    
    # # quantum setting
    # for i in range(0,6):
    #     for j in range(0,6):
    #         nostradamus(7,i,j,int(16/7),True)

    nostradamus(6,1,3,int(16/3),False)
