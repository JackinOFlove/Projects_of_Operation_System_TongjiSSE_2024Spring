(function (window) {
    //定义内存块、指令序列和缺页统计次数
    var Memory = [];
    var Instruction = [];
    var numMissingPage = 0;

    //获取页面的document
    var document = window.document;

    //获取页面上Start和Clear两个按键
    var startButton = document.getElementById("Start_button");
    var clearButton = document.getElementById("Clear_button");

    //获取页面上缺页次数和缺页率两个标签
    var pageMissingCount = document.getElementById("Numbers_of_Missing_Page");
    var pageFaultRate = document.getElementById("Page_Fault_Rate");

    //获取页面上三个参数的文本，并且转化为整数类型
    var numMemoryBlock = parseInt(document.getElementById("Number_of_Memory_Blocks").textContent);
    var numTotalInstruction = parseInt(document.getElementById("Number_of_Total_Instructions").textContent);
    var numInstructionPerPage = parseInt(document.getElementById("Number_of_Instructions_Per_Page").textContent);

    //执行指令函数
    function executeInstructions() {
        //获取页面上所选择的算法
        var chooseAlgorithm = document.querySelector("input:checked").value;
        if (chooseAlgorithm == "FIFO")
            fifoSimulation();
        else
            lruSimulation();
    }

    //判断是否缺页函数
    function judgeAvailable(instruction) {
        //遍历四个内存块，检查是否有内存块包含该指令所在的页面
        for (var i = 0; i < Memory.length; i++)
            if (Math.floor(instruction / numInstructionPerPage) === Memory[i])
                return true;
        return false;
    }

    //FIFO算法的实现函数
    function fifoSimulation() {
        //fifoBlock:用来记录最先到达的指令
        var fifoBlock = 0;

        for (var Index = 0; Index < Instruction.length; Index++) {
            //获得当前所需执行的指令
            curInstruction = Instruction[Index];
            var removePage = -1;
            //获得当前所需执行的指令的页面并且判断是否缺页
            var currentPage = Math.floor(curInstruction / numInstructionPerPage);
            var instructionAvailable = judgeAvailable(curInstruction);

            //如果缺页
            if (!instructionAvailable) {
                //设置缺页相关的参数
                numMissingPage++;
                pageMissingCount.textContent = numMissingPage;
                pageFaultRate.textContent = numMissingPage / numTotalInstruction;

                //记录被移除页面页号和更新当前页面
                removePage = Memory[(fifoBlock) % 4];
                Memory[(fifoBlock++) % 4] = currentPage;
            };
            //将新的一行添加入结果显示表格中
            addInstructionsToTable(Index, instructionAvailable, (fifoBlock - 1) % 4 + 1, removePage);
        };
    }

    //LRU算法的实现函数
    function lruSimulation() {
        //访问顺序数组，越靠后越近访问
        var orderSequence = [0, 1, 2, 3];

        for (var Index = 0; Index < Instruction.length; Index++) {
            //获得当前所需执行的指令
            curInstruction = Instruction[Index];
            var removePage = -1;
            //获得当前所需执行的指令的页面并且判断是否缺页
            var currentPage = Math.floor(curInstruction / numInstructionPerPage);
            var instructionAvailable = judgeAvailable(curInstruction);

            //如果缺页
            if (!instructionAvailable) {
                //设置缺页相关的参数
                numMissingPage++;
                pageMissingCount.textContent = numMissingPage;
                pageFaultRate.textContent = numMissingPage / numTotalInstruction;

                //记录被移除页面页号和更新当前页面
                removePage = Memory[orderSequence[0]];
                Memory[orderSequence[0]] = currentPage;
            };
            //记录当前使用页面的所在内存块
            var lruBlock = Memory.indexOf(currentPage);
            //从指令序列中删去当前块号
            orderSequence.splice(orderSequence.indexOf(lruBlock), 1);
            //将当前块号重新加入队尾(即最大的下标，最近使用)
            orderSequence.push(lruBlock);

            //将新的一行添加入结果显示表格中
            addInstructionsToTable(Index, instructionAvailable, lruBlock + 1, removePage);
        };
    }

    //生成指令序列的函数
    function generateInstructions() {
        var Index = 0;
        var preInstruction = -1;
        //在0-319中随机生成一条指令
        var curInstruction = Math.floor(Math.random() * numTotalInstruction);
        //将这一条指令放在指令序列的第一个
        Instruction[0] = curInstruction;

        //循环生成剩下的指令序列
        while (Index < numTotalInstruction - 1) {
            preInstruction = curInstruction;

            //50%的指令是顺序执行的
            if (Index % 2 === 0 && curInstruction < numTotalInstruction - 1)
                curInstruction++;

            //25%的指令是均匀分布在后地址的
            else if (Index % 4 === 1 && curInstruction < numTotalInstruction - 2)
                curInstruction = Math.floor(Math.random() * (numTotalInstruction - curInstruction - 2)) + curInstruction + 2;

            //25%的指令是均匀分布在前地址的
            else if (Index % 4 === 3 && curInstruction > 0)
                curInstruction = Math.floor(Math.random() * curInstruction);

            //如果两次生成的指令同一条，则随机再生成一条指令
            else {
                while (preInstruction === curInstruction)
                    curInstruction = Math.floor(Math.random() * numTotalInstruction);
            }
            //将生成的指令加到指令序列中
            Instruction[++Index] = curInstruction;
        }
    }

    //更新并显示表格内容的函数
    function addInstructionsToTable(index, instructionAvailable, block, removePage) {
        var curInstruction = Instruction[index];

        //每一条指令都插入新建的一行中
        var newRow = document.getElementById("showTable").insertRow()
        //每一行的第1个单元格：序号
        newRow.insertCell(0).innerHTML = index + 1;
        //每一行的第2个单元格：指令编号
        newRow.insertCell(1).innerHTML = "NO. " + curInstruction;

        //每一行的第3、4、5、6个单元格：存放页面的页号或者是空的
        for (var i = 0; i < 4; i++)
            newRow.insertCell(i + 2).innerHTML = Memory[i] == undefined ? "Empty" : Memory[i];

        //每一行的第7、8个单元格，判断是否缺页和载入、移出情况
        if (!instructionAvailable) {
            //如果缺页，显示缺页情况和载入块号、移出页号
            newRow.insertCell(6).innerHTML = "Yes";
            newRow.insertCell(7).innerHTML = block;
            if (removePage == -1 || removePage == undefined)
                newRow.insertCell(8).innerHTML = "- - -";
            else
                newRow.insertCell(8).innerHTML = removePage;
        }
        else {
            //如果不缺页，显示No
            newRow.insertCell(6).innerHTML = "No";
            newRow.insertCell(7).innerHTML = "- - -";
            newRow.insertCell(8).innerHTML = "- - -";
        }
    }

    //清除函数，重置信息
    function Clear() {
        //重置三个全局变量
        Memory = new Array(numMemoryBlock);
        Instruction = new Array(numTotalInstruction);
        numMissingPage = 0;

        //删除目前存在的表格信息
        var showTable = document.getElementById("showTable");
        while (showTable.rows.length > 1)
            showTable.deleteRow(1);

        //将调页结果设为NULL
        pageMissingCount.textContent = "NULL";
        pageFaultRate.textContent = "NULL";
    }

    //开始函数，开始执行
    function Start() {
        //先disable两个按键
        startButton.disabled = true;
        clearButton.disabled = true;

        //再清除已有信息、生成指令序列、执行指令
        Clear();
        generateInstructions();
        executeInstructions();

        //最后将两个按键再次置为可以使用状态
        startButton.disabled = false;
        clearButton.disabled = false;
    }

    //绑定事件触发类型
    startButton.addEventListener('click', Start);
    clearButton.addEventListener('click', Clear);
})(window)