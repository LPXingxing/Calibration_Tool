#include <stdio.h>

#include <stdlib.h>

#include <sys/ioctl.h>
#include <errno.h>
#include <linux/i2c.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/types.h>
#include <linux/types.h>

#include <linux/i2c-dev.h>

#define uint32_t unsigned int
#define uint8_t unsigned char
#define unint_8 unsigned char


#define MAX_RADIAL_COEFFICIENTS 6
#define MAX_TANGENTIAL_COEFFICIENTS 2
#define MAX_FISHEYE_COEFFICIENTS 6


__u8 read_register_8(int fd,__u8 chip_add, __u8 add)
{
	struct i2c_msg i2c_msg = {0};
	struct i2c_rdwr_ioctl_data i2cdev_data = {0};
	struct i2c_msg msgs[2];
	__u8 buf[3] = {0x00};
	__u8 buf_r[3] = {0x00};
	int ret = 0;

	buf[0] = add;
	msgs[0].addr= chip_add;
	msgs[0].flags = 0;//write
	msgs[0].len= 1;
	msgs[0].buf= buf;

	msgs[1].addr= chip_add;
	msgs[1].flags|= I2C_M_RD;
	msgs[1].len= 1;
	msgs[1].buf= buf_r;
	i2cdev_data.nmsgs= 2;
	i2cdev_data.msgs= msgs;

	ret=ioctl(fd,I2C_RDWR,&i2cdev_data);
	if(ret<0)
	{
		perror("ioctl error2");
	}

	return buf_r[0];


}



/**
 * Extrinsic parameters shared by camera and IMU.
 * All rotation + translation with respect to the same reference point
 */
struct extrinsics {     //24 bytes
	/**
	 * Rotation parameter expressed in Rodrigues notation.
	 * angle = sqrt(rx^2+ry^2+rz^2)
	 * unit axis = [rx,ry,rz]/angle
	 */
	float rx, ry, rz;
	/**
	 * Translation parameter from one camera to another parameter
	 */
	float tx, ty, tz;
};

/**
 * Coefficients as per distortion model (wide FOV) being used.
 */
struct fisheye_lens_distortion_coeff {     //32 bytes
	/**
	 * Radial coefficients count
	 */
	uint32_t coeff_count;     //4bytes
	/**
	 * Radial coefficients
	 */
	float k[MAX_FISHEYE_COEFFICIENTS];   //24 bytes
	/**
	 * 0 -> equidistant, 1 -> equisolid, 2 -> orthographic,
	 * 3 -> stereographic
	 */
	uint32_t mapping_type;          //4bytes
};
/**
 * Coefficients as per distortion model being used
 */
struct polynomial_lens_distortion_coeff {    //36 bytes
	/**
	 * Radial coefficients count
	 */
	uint32_t radial_coeff_count;    //4 bytes
	/**
	 * Radial coefficients
	 */
	float k[MAX_RADIAL_COEFFICIENTS];  //4*5 bytes
	/**
	 * Tangential coefficients count
	 */
	uint32_t tangential_coeff_count;    //4 bytes
	/**
	 * Tangential coefficients
	 */
	float p[MAX_TANGENTIAL_COEFFICIENTS]; //4*2 bytes
};
/**
 * IMU parameters
 */
struct imu_params {    //60 bytes
	/**
	 * 3D vector to add to accelerometer readings
	 */
	float linear_acceleration_bias[3];    //4*3 bytes
	/**
	 * 3D vector to add to gyroscope readings
	 */
	float angular_velocity_bias[3];        //4*3 bytes
	/**
	 * gravity acceleration
	 */
	float gravity_acceleration[3];        //4*3 bytes
	/**
	 * Extrinsic structure for IMU device
	 */
	struct extrinsics extr;      //24 bytes
};



/**
 * Camera Intrinsic parameters
 */
struct camera_intrinsics {
	/**
	 * Width and height of image in pixels
	 */
	uint32_t width, height;    //4*2 bytes
	/**
	 * Focal length in pixels    
	 */
	float fx, fy;                  //4*2 bytes
	/**
	 * skew
	 */
	float skew;                  //4 bytes
	/**
	 * Principal point (optical center) in pixels
	 */
	float cx, cy;                     //4*2 bytes
	/**
	 * Structure for distortion coefficients as per the model being used
	 * 0: pinhole, assuming polynomial distortion
	 * 1: fisheye, assuming fisheye distortion)
	 * 2: ocam (omini-directional)
	 */
	uint32_t distortion_type;    //4 bytes

	union distortion_coefficients   
	{
		struct polynomial_lens_distortion_coeff poly;     //36bytes
		struct fisheye_lens_distortion_coeff fisheye;    //32 bytes
	} dist_coeff;
};

/**
 * Main structure for ISAAC parameters
 */
struct syncSensor_params {
	/**
	 * EEPROM layout version
	 */
	uint32_t version;     //4
	/**
	 * Factory Blob Flag, to set when factory flashed and reset to 0
	 * when user modified
	 */
	int factory_data;  //4
	/**
	 * Intrinsic structure for camera device
	 */
	struct camera_intrinsics left_cam_intr;  
	struct camera_intrinsics right_cam_intr;  
	/**
	 * Extrinsic structure for camera device
	 */
	struct extrinsics cam_extr;
	/**
	 * Flag for IMU 0-absent, 1-present
	 */
	unint_8 imu_present;
	/**
	 * Intrinsic structure for IMU
	 */
	struct imu_params imu;
};

union eeprom_storage {
	struct syncSensor_params para;
	unsigned char s[256];

};


int main(int argc, void **argv)
{

	printf("eeprom parameter size = %ld \n",sizeof(struct syncSensor_params));
	struct extrinsics cam_extrin = {0};
	cam_extrin.rx = 0.002599;
	cam_extrin.ry = -0.001930;
	cam_extrin.rz = -0.002435;
	cam_extrin.tx = -2.167833;
	cam_extrin.ty = -0.056156;
	cam_extrin.tz = 0.108474;


	//struct fisheye_lens_distortion_coeff cam1_fieye_dist_coeff;

	struct polynomial_lens_distortion_coeff cam1_poly_dist_coeff = {0};
	cam1_poly_dist_coeff.radial_coeff_count = 6;
	cam1_poly_dist_coeff.k[0] = 0.196140;
	cam1_poly_dist_coeff.k[1] = -0.075394;
	cam1_poly_dist_coeff.k[2] = -0.000764;
	cam1_poly_dist_coeff.k[3] = 0.560068;
	cam1_poly_dist_coeff.k[4] = -0.087285;
	cam1_poly_dist_coeff.k[5] = -0.013044;
	cam1_poly_dist_coeff.tangential_coeff_count = 2;
	cam1_poly_dist_coeff.p[0] = -0.000384;
	cam1_poly_dist_coeff.p[1] = 0.000433;

	struct polynomial_lens_distortion_coeff cam2_poly_dist_coeff = {0};
	cam2_poly_dist_coeff.radial_coeff_count = 6;
	cam2_poly_dist_coeff.k[0] = 31.362768;
	cam2_poly_dist_coeff.k[1] = 14.978426;
	cam2_poly_dist_coeff.k[2] = 0.347907;
	cam2_poly_dist_coeff.k[3] = 31.808109;
	cam2_poly_dist_coeff.k[4] = 26.611555;
	cam2_poly_dist_coeff.k[5] = 3.004494;
	cam2_poly_dist_coeff.tangential_coeff_count = 2;
	cam2_poly_dist_coeff.p[0] = -0.000867;
	cam2_poly_dist_coeff.p[1] = 0.000119;

	struct camera_intrinsics cam1_intrinsics = {0};
	cam1_intrinsics.width = 1920;
	cam1_intrinsics.height = 1200;
	cam1_intrinsics.fx = 959.363953;
	cam1_intrinsics.fy = 959.699036;
	cam1_intrinsics.cx = 948.305786;
	cam1_intrinsics.cy = 612.527283;
	cam1_intrinsics.skew = 0;
	cam1_intrinsics.distortion_type = 0;
	cam1_intrinsics.dist_coeff.poly = cam1_poly_dist_coeff;	
	struct camera_intrinsics cam2_intrinsics = {0};
	cam2_intrinsics.width = 1920;
	cam2_intrinsics.height = 1200;
	cam2_intrinsics.fx = 961.953735;
	cam2_intrinsics.fy = 963.809143;
	cam2_intrinsics.cx = 953.546570;
	cam2_intrinsics.cy = 621.811890;
	cam2_intrinsics.skew = 0;
	cam2_intrinsics.distortion_type = 0;
	cam2_intrinsics.dist_coeff.poly = cam2_poly_dist_coeff;




	struct imu_params hawk_imu_params = {0};



	struct syncSensor_params hawk_param = {0};
	hawk_param.version = 1;
	hawk_param.factory_data = 0;
	hawk_param.left_cam_intr = cam1_intrinsics;
	hawk_param.right_cam_intr = cam2_intrinsics;
	hawk_param.cam_extr = cam_extrin;
	hawk_param.imu_present = 1;
	hawk_param.imu = hawk_imu_params;


#if 1
	union eeprom_storage eeprom_bin = {0};
	unsigned char str[1024] =  {0};
	eeprom_bin.para=hawk_param;
	int i = 0;
	for(i = 0; i < 256; i++)
	{
		sprintf(str, "i2ctransfer -f -y 30 w2@0x%02x 0x%x 0x%x", 0x54+i/256, i&0xff, eeprom_bin.s[i]);
		printf("%s\n", str);
		system(str);
	}
	printf("left_cam_intr.fx = 0x%x\n", *(int *)(&hawk_param.left_cam_intr.fx));
	printf("left_cam_intr.fx = 0x%x\n", *(int *)(&hawk_param.right_cam_intr.fx));
#endif
	return 0;

}
