# -*- coding: utf-8 -*-
from selenium import webdriver

# 导入显示等待类
from selenium.webdriver.support.ui import WebDriverWait

# 导入期望类
from selenium.webdriver.support import expected_conditions as EC

# 导入By类
from selenium.webdriver.common.by import By

# 导入异常类
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import ActionChains
import time
from PIL import Image


class HuXiu:

    def __init__(self):
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 20, 0.5)

    def get_register_button(self):
        """
        获取注册按钮
        :return: 返回注册按钮对象
        """
        self.driver.get("https://www.huxiu.com/")
        self.driver.maximize_window()
        try:
            button = self.wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "js-register"))
            )
        except TimeoutException as e:
            print("get_register_button Error:" + e)
        except NoSuchElementException as e:
            print("get_register_button Error:" + e)
        return button

    def get_slider(self):
        """
        获得滑块
        :return: 返回滑块对象
        """
        try:
            slider = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "gt_slider_knob"))
            )
        except TimeoutException as e:
            print("get_slider Error:" + e)
        except NoSuchElementException as e:
            print("get_slider Error:" + e)
        return slider

    def get_position(self):
        """
        获取验证码位置
        :return: 返回验证码位置元组
        """
        slider = self.get_slider()
        ActionChains(self.driver).move_to_element(slider).perform()
        img = self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "gt_fullbg"))
        )
        time.sleep(2)
        location = img.location
        size = img.size
        top, bottom, left, right = (
            location["y"],
            location["y"] + size["height"],
            location["x"],
            location["x"] + size["width"],
        )
        return (top, bottom, left, right)

    def get_geetest_image(self):
        """
        获取验证码图片
        :return: 返回图片对象
        """
        top, bottom, left, right = self.get_position()
        self.driver.save_screenshot("captcha.png")
        image = Image.open("captcha.png")
        image = image.crop((left, top, right, bottom))

        # 展示截图便于调试
        # image.show()
        return image

    def get_geetest_image2(self):
        """
        获取带缺口验证码图片
        :return: 图片对象
        """
        # 点击呼出缺口
        slider = self.get_slider()
        slider.click()
        captcha = self.get_geetest_image()
        return captcha

    def is_pixel_equal(self, image1, image2, x, y):
        """
        判断两个像素是否相同
        :param image1: 不带缺口图片
        :param image2: 带缺口图片
        :param x: 位置x
        :param y: 位置y
        :return: 像素是否相同
        """
        pixel1 = image1.load()[x, y]
        pixel2 = image2.load()[x, y]
        threshold = 60
        if (
            abs(pixel1[0] - pixel2[0]) < threshold
            and abs(pixel1[1] - pixel2[1]) < threshold
            and abs(pixel1[2] - pixel2[2]) < threshold
        ):
            return True
        else:
            return False

    def get_gap(self, image1, image2):
        """
        获取缺口偏移liang
        :param image1: 不带缺口图片
        :param image2: 带缺口图片
        :return: 返回偏移值
        """
        left = 60
        for i in range(left, image1.size[0]):
            for j in range(image1.size[1]):
                if not self.is_pixel_equal(image1, image2, i, j):
                    left = i
                    return left
        return left

    def get_track(self, distance):
        """
        根据偏移量获取移动轨迹
        :param distance: 偏移量
        :return: 移动轨迹
        """
        # 移动轨迹
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
                a = 3
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

    def move_to_gap(self, slider, tracks):
        """
        拖动滑块到缺口处
        :param slider: 滑块
        :param tracks: 轨迹
        :return:
        """
        #
        ActionChains(self.driver).click_and_hold(slider).perform()
        for x in tracks:
            ActionChains(self.driver).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(0.5)
        ActionChains(self.driver).release().perform()

    def main(self):
        button = self.get_register_button()
        button.click()
        image1 = self.get_geetest_image()
        imaeg2 = self.get_geetest_image2()
        distance = self.get_gap(image1, imaeg2)
        slider = self.get_slider()
        track = self.get_track(distance)
        self.move_to_gap(slider, track)


if __name__ == "__main__":
    hx = HuXiu()
    hx.main()
