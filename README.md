# 虎嗅网极验证码识别  
在学习了极验证码的破解后，一直想找一个网站练手，于是就发现了[虎嗅网](https://www.huxiu.com/)，当注册虎嗅网时会弹出极验证码，以此为背景开始破解，在这里我使用的是python + selenium。  

1. 在浏览器上熟悉下操作步骤，打开虎嗅网网址，点击注册，会弹出注册框：  
![注册框](https://github.com/zloveh/Geetest/blob/master/image/hx/a1.png)  
当鼠标移动到画块上时，图片会显示出来：  
![图片](https://github.com/zloveh/Geetest/blob/master/image/hx/a2.png)  
当点击滑块时会显示带缺口的图片：  
![缺口](https://github.com/zloveh/Geetest/blob/master/image/hx/a3.png)  
之后就是拖动滑块到缺口位置了。  
&emsp;&emsp;我们要做的主要就是找到缺口位置，之后驱动滑块滑到此位置，找缺口就是对比没有缺口的图片和有缺口的图片的像素，超出一定阈值则返回此像素的位置，然后让滑块滑到此位置，但也不能直接滑到此位置，我们要处理滑块的滑动轨迹，尽量使它象人为手动的，不然还会被检测出来，导致滑动失败。   

2. 熟悉以上流程后，开始写代码：   
先获取注册按钮：
在浏览器中检查元素，找到`注册`的位置：  
![注册](https://github.com/zloveh/Geetest/blob/master/image/hx/b1.png)  
代码:  
    button = self.wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "js-register"))
            )  
        
3. 获取滑块:  
![滑块](https://github.com/zloveh/Geetest/blob/master/image/hx/b2.png)  
代码：  
    slider = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "gt_slider_knob"))  )    
   
4. 获取验证码位置：  
![位置](https://github.com/zloveh/Geetest/blob/master/image/hx/b3.png)  
代码：   
首先获取滑块：   
    slider = self.get_slider()     
想要获取验证码只有先把鼠标移动到滑块上，验证码图片才会显示出来：  
    ActionChains(self.driver).move_to_element(slider).perform()  
    img = self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "gt_fullbg"))
        )  
    time.sleep(2)    
获取验证码图片位置{x, y}：
    location = img.location    
获取验证码图片大小{width, height}：  
    size = img.size    
获取图片在浏览器窗口中的具体位置(左上角坐标，右下角坐标)：  
    top, bottom, left, right = (  
            location["y"],   
            location["y"] + size["height"],  
            location["x"],  
            location["x"] + size["width"],  
        )  
          
5. 获取无缺口的验证码图片：  
代码：  
先对整个网页截图：  
driver.save_screenshot("captcha.png")  
根据图片在浏览器中的坐标把图片截取下来，在这里使用了pillow库：    
from PIL import Image  
    image = Image.open("captcha.png")  
    image = image.crop((left, top, right, bottom))    
    展示截图便于调试  
    image.show()  

6. 获取带缺口的验证码图片：    
代码：  
点击滑块，使得带缺口的验证码显示出来：  
    slider.click()  
由于图片位置什么都没有变化，所以截图可以参考步骤5

7. 比较两张图片像素，如果它们的差值在一定范围，则认为相同，继续比较下一个像素，超出范围则认为找到了缺口位置，返回这个位置：  
代码：   
    加载[x, y]位置的像素   
    pixel1 = image1.load()[x, y]  
    pixel2 = image2.load()[x, y]   
    阈值设置为60   
    threshold = 60    
    由于是RGB图像，所以要分别比较三原色的值  
        if (  
        &emsp;&emsp;abs(pixel1[0] - pixel2[0]) < threshold  
        &emsp;&emsp;and abs(pixel1[1] - pixel2[1]) < threshold  
        &emsp;&emsp;and abs(pixel1[2] - pixel2[2]) < threshold  
        ):  
        return True  
        else:  
        &emsp;&emsp;return False  
    把这些代发封装为：is_pixel_equal(self, image1, image2, x, y)h函数

    比较全部的两张图片：  
    从60像素的位置开始比较  
        left = 60  
            &emsp;&emsp;for i in range(left, image1.size[0]):  
                &emsp;&emsp;&emsp;&emsp;for j in range(image1.size[1]):  
                    &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;if not self.is_pixel_equal(image1, image2, i, j):   
                        &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;left = i  
                        &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;return left  
            &emsp;&emsp;return left  
    left就是缺口位置。  

8. 由于要避免检查出非人为拖动而导致失败，所以设计移动轨迹  
根据偏移量获取移动轨迹,distance: 偏移量:  
代码:  
    ### 移动轨迹
        #轨迹列表
        track = []
        # 当前位移
        current = 0
        # 减速阈值
        mid = distance * 4 / 5
        # 计算间隔
        t = 0.2
        # 初速度
        v = 0
        while current < distance:
            if current < mid:
                # 加速度
                a = 2
            else:
                a = -3
            v0 = v
            # 当前速度v = v0 + a*t
            v = v0 + a * t
            # 移动距离x = v0*t + 1/2*a*t*t
            move = v0 * t + 1 / 2 * a * t * t
            # 当前位移
            current += move
            # 加入轨迹
            track.append(round(move))
        # 由于move是取的绝对值，所以最后滑块移动的距离和distance肯定会有偏差，
        # 在移动轨迹最后添加一个修正量，具体添加多少视情况而定
        track.append(-4)
        return track  

9. 最后依据轨迹进行拖动滑块:  
代码：  
slider为滑块对象   
tracks为轨迹列表  
    #####
        ActionChains(self.driver).click_and_hold(slider).perform()
        for x in tracks:
            ActionChains(self.driver).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(0.5)
        ActionChains(self.driver).release().perform()  

10. 完整代码：虎嗅网极验破解.py  
![成果](https://github.com/zloveh/Geetest/blob/master/image/hx/c1.png)
